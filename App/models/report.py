from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from App.database.db import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    institution = Column(String, index=True)
    description = Column(Text)
    category = Column(String, nullable=True)
    location = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    status = Column(String, default="submitted")
    is_anonymous = Column(Integer, default=0)
    assigned_department = Column(String, nullable=True)
    official_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    location_id = Column(Integer, ForeignKey("campus_locations.id"), nullable=True)
