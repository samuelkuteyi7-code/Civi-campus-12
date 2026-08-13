from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from App.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    institution = Column(String, index=True)
    department = Column(String, nullable=True)
    matric_number = Column(String, nullable=True)
    role = Column(String, default="student")
    token = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
