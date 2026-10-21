from sqlalchemy import delete
from database import SessionLocal
from models import Price

db = SessionLocal()
result = db.execute(delete(Price).where(Price.source == "demo"))
db.commit()
db.close()
print(f"Demo rows deleted: {result.rowcount}")