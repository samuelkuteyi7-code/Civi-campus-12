from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from App.database.db import Base


class DebateRoom(Base):
    __tablename__ = "debate_rooms"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    institution = Column(String, index=True)
    question = Column(String)
    description = Column(Text, nullable=True)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)


class DebateArgument(Base):
    __tablename__ = "debate_arguments"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("debate_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    position = Column(String)
    text = Column(Text)
    evidence_url = Column(String, nullable=True)
    has_evidence = Column(Integer, default=0)
    ai_moderation_note = Column(Text, nullable=True)
    is_duplicate = Column(Integer, default=0)
    is_flagged = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
