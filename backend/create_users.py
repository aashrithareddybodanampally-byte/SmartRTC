from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

admin = User(
    username="admin",
    password=pwd_context.hash("admin123"),
    role="admin"
)

driver = User(
    username="driver1",
    password=pwd_context.hash("driver123"),
    role="driver",
    employee_id="DRV001"
)

conductor = User(
    username="conductor1",
    password=pwd_context.hash("conductor123"),
    role="conductor",
    employee_id="CON001"
)

db.add_all([admin, driver, conductor])
db.commit()
db.close()

print("Users created successfully.")