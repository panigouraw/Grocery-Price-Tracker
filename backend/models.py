from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint, Index
)
from database import Base


class State(Base):
    __tablename__ = "gp_states"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class District(Base):
    __tablename__ = "gp_districts"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    state_id = Column(Integer, ForeignKey("gp_states.id"), nullable=False)
    __table_args__ = (UniqueConstraint("state_id", "name", name="uq_state_district"),)


class Item(Base):
    __tablename__ = "gp_items"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(30), nullable=False)  # vegetable / fruit / grocery
    unit = Column(String(20), default="kg")


class Price(Base):
    __tablename__ = "gp_prices"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("gp_items.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("gp_districts.id"), nullable=False)
    market = Column(String(150), nullable=False)
    price_date = Column(Date, nullable=False)
    min_price = Column(Float)     # Rs per kg
    max_price = Column(Float)     # Rs per kg
    modal_price = Column(Float)   # Rs per kg (most common price)
    source = Column(String(30), default="agmarknet")
    __table_args__ = (
        UniqueConstraint("item_id", "district_id", "market", "price_date", name="uq_price_row"),
        Index("ix_price_district_date", "district_id", "price_date"),
    )