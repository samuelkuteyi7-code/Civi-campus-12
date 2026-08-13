from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from App.database.db import Base


class SUGProfile(Base):
    __tablename__ = "sug_profiles"

    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String, index=True)
    name = Column(String)
    position = Column(String)   # e.g. "President", "Welfare Director"
    term = Column(String, nullable=True)   # e.g. "2026/2027"
    photo_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
