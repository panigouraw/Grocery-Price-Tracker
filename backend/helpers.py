from sqlalchemy import select
from models import State, District, Item


def get_or_create_state(db, name):
    obj = db.execute(select(State).where(State.name == name)).scalar_one_or_none()
    if obj is None:
        obj = State(name=name)
        db.add(obj)
        db.flush()
    return obj


def get_or_create_district(db, state_id, name):
    obj = db.execute(
        select(District).where(District.state_id == state_id, District.name == name)
    ).scalar_one_or_none()
    if obj is None:
        obj = District(state_id=state_id, name=name)
        db.add(obj)
        db.flush()
    return obj


def get_or_create_item(db, name, category, unit="kg"):
    obj = db.execute(select(Item).where(Item.name == name)).scalar_one_or_none()
    if obj is None:
        obj = Item(name=name, category=category, unit=unit)
        db.add(obj)
        db.flush()
    return obj