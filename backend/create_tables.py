from database import engine, Base
import models  # noqa: F401  (needed so tables are registered)

Base.metadata.create_all(bind=engine)
print("Tables created successfully")
