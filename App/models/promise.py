from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from App.database.db import Base


class Promise(Base):
    __tablename__ = "promises"

    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    department = Column(String, nullable=True)
    status = Column(String, default="not_started")   # not_started, in_progress, completed
    percent_complete = Column(Integer, default=0)
    due_date = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
