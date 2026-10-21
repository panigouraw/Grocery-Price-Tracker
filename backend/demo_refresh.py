import random
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, insert, select

from database import SessionLocal
from models import Item, Price
from seed_demo import ITEMS

BASE_PRICE = {name: base for name, _category, base in ITEMS}
_lock = threading.Lock()


def today_ist():
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def add_missing_days():
    """Adds demo prices for every day after the latest demo day, up to today."""
    db = SessionLocal()
    try:
        latest = db.scalar(select(func.max(Price.price_date)).where(Price.source == "demo"))
        today = today_ist()
        if latest is None or latest >= today:
            return 0

        names = {i.id: i.name for i in db.execute(select(Item)).scalars()}
        last_rows = db.execute(
            select(Price.item_id, Price.district_id, Price.modal_price).where(
                Price.source == "demo", Price.price_date == latest
            )
        ).all()
        current = {(i, d): p for i, d, p in last_rows}

        rnd = random.Random()
        rows = []
        day = max(latest, today - timedelta(days=30))
        while day < today:
            day += timedelta(days=1)
            for key, price in list(current.items()):
                price = price * rnd.uniform(0.97, 1.03)
                base = BASE_PRICE.get(names.get(key[0]))
                if base:
                    price = min(max(price, base * 0.7), base * 1.4)
                current[key] = price
                modal = round(price, 2)
                rows.append({
                    "item_id": key[0],
                    "district_id": key[1],
                    "market": "Demo Market",
                    "price_date": day,
                    "min_price": round(modal * 0.9, 2),
                    "max_price": round(modal * 1.1, 2),
                    "modal_price": modal,
                    "source": "demo",
                })

        db.execute(insert(Price), rows)
        # keep the database small: delete demo rows older than 60 days
        db.execute(delete(Price).where(
            Price.source == "demo", Price.price_date < today - timedelta(days=60)
        ))
        db.commit()
        return len(rows)
    finally:
        db.close()


def demo_refresh():
    """Safe wrapper: never crashes the server, never runs twice at once."""
    if not _lock.acquire(blocking=False):
        return
    try:
        added = add_missing_days()
        if added:
            print(f"Demo refresh: added {added} price rows")
    except Exception as err:  # noqa: BLE001
        print("Demo refresh failed:", err)
    finally:
        _lock.release()