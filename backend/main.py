import os
import threading
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

load_dotenv()

from database import Base, engine, get_db  # noqa: E402
from models import District, Item, Price, State  # noqa: E402
from helpers import (  # noqa: E402
    get_or_create_district, get_or_create_item, get_or_create_state,
)

ADMIN_KEY = os.getenv("ADMIN_KEY", "")


def safe_import():
    """Runs the Agmarknet import and never crashes the server."""
    try:
        from fetch_agmarknet import run_import
        run_import()
    except Exception as err:  # noqa: BLE001
        print("Daily import failed:", err)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler = None
    real_on = os.getenv("ENABLE_SCHEDULER", "0") == "1"
    demo_on = os.getenv("DEMO_AUTO_REFRESH", "0") == "1"
    if real_on or demo_on:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
        if real_on:
            scheduler.add_job(safe_import, "cron", hour=7, minute=0)
            scheduler.add_job(safe_import, "cron", hour=16, minute=0)
        if demo_on:
            from demo_refresh import demo_refresh
            scheduler.add_job(demo_refresh, "cron", hour=0, minute=10)
            # also runs once every time the server wakes up
            threading.Thread(target=demo_refresh, daemon=True).start()
        scheduler.start()
        print("Scheduler started")
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Grocery Price Tracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_admin(x_admin_key: str = Header(default="")):
    if not ADMIN_KEY or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")


@app.get("/")
def home():
    return {"message": "Grocery Price Tracker API is running"}


@app.get("/states")
def list_states(db: Session = Depends(get_db)):
    rows = db.execute(select(State).order_by(State.name)).scalars().all()
    return [{"id": s.id, "name": s.name} for s in rows]


@app.get("/districts")
def list_districts(state_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        select(District).where(District.state_id == state_id).order_by(District.name)
    ).scalars().all()
    return [{"id": d.id, "name": d.name} for d in rows]


@app.get("/prices")
def get_prices(
    district_id: int,
    category: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    latest = db.scalar(
        select(func.max(Price.price_date)).where(Price.district_id == district_id)
    )
    if latest is None:
        return {"latest_date": None, "items": []}

    since = latest - timedelta(days=14)
    stmt = (
        select(Price, Item)
        .join(Item, Item.id == Price.item_id)
        .where(Price.district_id == district_id, Price.price_date >= since)
    )
    if category and category != "all":
        stmt = stmt.where(Item.category == category)
    if q:
        stmt = stmt.where(Item.name.ilike(f"%{q}%"))

    # item_id -> date -> list of prices from different markets
    by_item = defaultdict(lambda: defaultdict(list))
    item_info = {}
    for price, item in db.execute(stmt).all():
        item_info[item.id] = item
        by_item[item.id][price.price_date].append(price)

    result = []
    for item_id, days in by_item.items():
        dates = sorted(days.keys())
        last_day = dates[-1]

        def avg(rows, field):
            values = [getattr(r, field) for r in rows if getattr(r, field) is not None]
            return round(sum(values) / len(values), 2) if values else None

        today_rows = days[last_day]
        current = avg(today_rows, "modal_price")
        previous = avg(days[dates[-2]], "modal_price") if len(dates) > 1 else None
        change = None
        change_pct = None
        if previous:
            change = round(current - previous, 2)
            change_pct = round(change / previous * 100, 1)

        item = item_info[item_id]
        result.append({
            "item_id": item_id,
            "name": item.name,
            "category": item.category,
            "unit": item.unit,
            "price": current,
            "min_price": avg(today_rows, "min_price"),
            "max_price": avg(today_rows, "max_price"),
            "date": last_day.isoformat(),
            "markets": len({r.market for r in today_rows}),
            "previous_price": previous,
            "change": change,
            "change_pct": change_pct,
            "source": today_rows[0].source,
        })

    result.sort(key=lambda x: x["name"])
    return {"latest_date": latest.isoformat(), "items": result}


@app.get("/history")
def get_history(
    item_id: int,
    district_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
):
    latest = db.scalar(
        select(func.max(Price.price_date)).where(
            Price.district_id == district_id, Price.item_id == item_id
        )
    )
    if latest is None:
        return []
    since = latest - timedelta(days=max(days, 1))
    rows = db.execute(
        select(Price.price_date, func.avg(Price.modal_price))
        .where(
            Price.district_id == district_id,
            Price.item_id == item_id,
            Price.price_date >= since,
        )
        .group_by(Price.price_date)
        .order_by(Price.price_date)
    ).all()
    return [{"date": d.isoformat(), "price": round(float(p), 2)} for d, p in rows]


class PriceIn(BaseModel):
    state: str
    district: str
    item: str
    category: str = "grocery"
    unit: str = "kg"
    price_per_kg: float
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_date: Optional[date] = None
    market: str = "Manual Entry"


@app.post("/admin/prices", dependencies=[Depends(check_admin)])
def add_price(body: PriceIn, db: Session = Depends(get_db)):
    when = body.price_date or date.today()
    state = get_or_create_state(db, body.state.strip())
    district = get_or_create_district(db, state.id, body.district.strip())
    item = get_or_create_item(db, body.item.strip(), body.category, body.unit)

    row = db.execute(
        select(Price).where(
            Price.item_id == item.id,
            Price.district_id == district.id,
            Price.market == body.market,
            Price.price_date == when,
        )
    ).scalar_one_or_none()
    if row is None:
        row = Price(
            item_id=item.id, district_id=district.id,
            market=body.market, price_date=when,
        )
        db.add(row)
    row.modal_price = body.price_per_kg
    row.min_price = body.min_price if body.min_price is not None else body.price_per_kg
    row.max_price = body.max_price if body.max_price is not None else body.price_per_kg
    row.source = "manual"
    db.commit()
    return {"saved": True, "item": item.name, "date": when.isoformat()}


@app.post("/admin/refresh", dependencies=[Depends(check_admin)])
def refresh_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(safe_import)
    return {"message": "Import started in background"}