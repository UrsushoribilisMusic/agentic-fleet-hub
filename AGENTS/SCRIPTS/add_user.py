from app.database import SessionLocal
from app.models import User
import os

db = SessionLocal()
user = User(full_name='Miguel Rodriguez', email='miguel@bigbearengineering.com', role='Admin')
db.add(user)
db.commit()
print('SUCCESS: User Miguel Rodriguez added to database')
