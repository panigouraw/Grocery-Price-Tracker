import os
import time
from collections import defaultdict
from datetime import datetime

import requests
from dotenv import load_dotenv
from sqlalchemy import select

from database import SessionLocal
from models import Price
from categories import get_category
from helpers import get_or_create_state, get_or_create_district, get_or_create_item

load_dotenv()

API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
PAGE_SIZE = 500


def get_states():
    raw = os.getenv("STATES", "Andhra Pradesh,Telangana")
    return [s.strip() for s in raw.split(",") if s.strip()]


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_date(text):
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except (TypeError, ValueError):
        return None


def fetch_state(state_name, api_key):
    records = []
    offset = 0
    while True:
        params = {
            "api-key": api_key,
            "format": "json",
            "limit": PAGE_SIZE,
            "offset": offset,
            "filters[state]": state_name,
        }
        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        batch = data.get("records", [])
        if not batch:
            break
        records.extend(batch)
        offset += len(batch)
        total = int(data.get("total", 0) or 0)
        if offset >= total:
            break
        time.sleep(0.5)
    return records


def save_records(db, state_name, records):
    state = get_or_create_state(db, state_name)
    district_ids = {}
    item_ids = {}
    grouped = defaultdict(list)

    for rec in records:
        price_date = parse_date(rec.get("arrival_date"))
        modal = to_float(rec.get("modal_price"))
        district_name = (rec.get("district") or "").strip()
        commodity = (rec.get("commodity") or "").strip()
        market = (rec.get("market") or "Unknown").strip()[:150]
        if price_date is None or not modal or modal <= 0:
            continue
        if not district_name or not commodity:
            continue
        low = to_float(rec.get("min_price")) or modal
        high = to_float(rec.get("max_price")) or modal

        if district_name not in district_ids:
            district_ids[district_name] = get_or_create_district(db, state.id, district_name).id
        if commodity not in item_ids:
            item_ids[commodity] = get_or_create_item(db, commodity, get_category(commodity)).id

        key = (item_ids[commodity], district_ids[district_name], market, price_date)
        grouped[key].append((low, high, modal))

    if not grouped:
        return 0

    existing = {}
    rows = db.execute(
        select(Price).where(
            Price.price_date.in_({k[3] for k in grouped}),
            Price.district_id.in_(list(district_ids.values())),
        )
    ).scalars()
    for row in rows:
        existing[(row.item_id, row.district_id, row.market, row.price_date)] = row

    saved = 0
    for key, values in grouped.items():
        n = len(values)
        # Agmarknet gives Rs per quintal (100 kg) -> convert to Rs per kg
        low = round(sum(v[0] for v in values) / n / 100, 2)
        high = round(sum(v[1] for v in values) / n / 100, 2)
        modal = round(sum(v[2] for v in values) / n / 100, 2)
        if key in existing:
            row = existing[key]
            row.min_price, row.max_price, row.modal_price = low, high, modal
            row.source = "agmarknet"
        else:
            db.add(Price(
                item_id=key[0], district_id=key[1], market=key[2],
                price_date=key[3], min_price=low, max_price=high,
                modal_price=modal, source="agmarknet",
            ))
        saved += 1
    return saved


def run_import():
    api_key = os.getenv("DATA_GOV_API_KEY", "").strip()
    if not api_key:
        raise ValueError("DATA_GOV_API_KEY is missing in backend/.env")

    db = SessionLocal()
    total = 0
    states = get_states()
    try:
        for state_name in states:
            records = fetch_state(state_name, api_key)
            print(f"{state_name}: {len(records)} records downloaded")
            total += save_records(db, state_name, records)
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Import finished. Rows saved or updated: {total}")
    return {"states": states, "saved": total}


if __name__ == "__main__":
    run_import()