from sqlalchemy import Column, String, Integer, DateTime
import datetime
from .base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="Analyst")  # e.g., Admin, Analyst
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
