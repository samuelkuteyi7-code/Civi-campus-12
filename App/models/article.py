from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from App.database.db import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    institution = Column(String, index=True)
    title = Column(String)
    category = Column(String, default="general")
    lead = Column(Text, nullable=True)
    body = Column(Text)
    image_url = Column(String, nullable=True)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
