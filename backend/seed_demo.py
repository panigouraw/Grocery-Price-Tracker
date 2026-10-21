import random
from datetime import date, timedelta
from sqlalchemy import delete, insert
from database import SessionLocal, engine, Base
from models import Price
from helpers import get_or_create_state, get_or_create_district, get_or_create_item
import models  # noqa: F401

DISTRICTS = {
    "Andhra Pradesh": [
        "Kadapa", "Tirupati", "Kurnool", "Anantapur", "Guntur",
        "Visakhapatnam", "Krishna", "East Godavari", "Chittoor",
    ],
    "Telangana": ["Hyderabad", "Warangal", "Karimnagar", "Nizamabad"],
    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli", "Vellore","hosur",
    ],
    "Karnataka": [
        "Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi", "Tumakuru",
    ],
}

# (name, category, base price in Rs per kg)
ITEMS = [
    ("Tomato", "vegetable", 30), ("Onion", "vegetable", 35),
    ("Potato", "vegetable", 32), ("Brinjal", "vegetable", 40),
    ("Bhindi (Ladies Finger)", "vegetable", 50), ("Carrot", "vegetable", 55),
    ("Cabbage", "vegetable", 25), ("Cauliflower", "vegetable", 45),
    ("Green Chilli", "vegetable", 70), ("Beans", "vegetable", 60),
    ("Beetroot", "vegetable", 40), ("Cucumber", "vegetable", 30),
    ("Drumstick", "vegetable", 90), ("Capsicum", "vegetable", 60),
    ("Banana", "fruit", 45), ("Apple", "fruit", 150), ("Mango", "fruit", 90),
    ("Orange", "fruit", 70), ("Papaya", "fruit", 35),
    ("Pomegranate", "fruit", 120), ("Grapes", "fruit", 80),
    ("Watermelon", "fruit", 20), ("Guava", "fruit", 50),
    ("Rice", "grocery", 55), ("Wheat", "grocery", 32),
    ("Toor Dal", "grocery", 150), ("Moong Dal", "grocery", 120),
    ("Sugar", "grocery", 45), ("Groundnut Oil", "grocery", 190),
    ("Sunflower Oil", "grocery", 130), ("Turmeric", "grocery", 140),
    ("Red Chilli (Dry)", "grocery", 220), ("Tamarind", "grocery", 180),
]

DAYS = 14


def main():
    Base.metadata.create_all(bind=engine)
    rnd = random.Random(42)
    db = SessionLocal()
    try:
        db.execute(delete(Price).where(Price.source == "demo"))
        today = date.today()
        rows = []
        for state_name, districts in DISTRICTS.items():
            state = get_or_create_state(db, state_name)
            for dname in districts:
                district = get_or_create_district(db, state.id, dname)
                district_factor = rnd.uniform(0.92, 1.08)
                for name, category, base in ITEMS:
                    item = get_or_create_item(db, name, category)
                    price = base * district_factor
                    for back in range(DAYS - 1, -1, -1):
                        price *= rnd.uniform(0.97, 1.03)
                        modal = round(price, 2)
                        rows.append({
                            "item_id": item.id,
                            "district_id": district.id,
                            "market": "Demo Market",
                            "price_date": today - timedelta(days=back),
                            "min_price": round(modal * 0.9, 2),
                            "max_price": round(modal * 1.1, 2),
                            "modal_price": modal,
                            "source": "demo",
                        })
        # one bulk insert is much faster than 6000 single inserts (important for cloud DB)
        db.execute(insert(Price), rows)
        db.commit()
        print(f"Demo data added: {len(rows)} price rows")
    finally:
        db.close()


if __name__ == "__main__":
    main()