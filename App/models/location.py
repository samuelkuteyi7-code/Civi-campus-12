from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from App.database.db import Base


class CampusLocation(Base):
    __tablename__ = "campus_locations"

    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String, index=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
