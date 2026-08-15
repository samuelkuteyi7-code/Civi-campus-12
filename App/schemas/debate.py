from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DebateRoomCreate(BaseModel):
    question: str
    description: Optional[str] = None
    article_id: Optional[int] = None


class ArgumentCreate(BaseModel):
    position: str
    text: str
    evidence_url: Optional[str] = None


class ArgumentResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    author_name: Optional[str] = None
    position: str
    text: str
    evidence_url: Optional[str] = None
    has_evidence: int
    ai_moderation_note: Optional[str] = None
    is_duplicate: int
    is_flagged: int
    created_at: datetime

    class Config:
        from_attributes = True


class SentimentBreakdown(BaseModel):
    support: int
    oppose: int
    undecided: int
    support_pct: float
    oppose_pct: float
    undecided_pct: float
    total: int


class DebateRoomResponse(BaseModel):
    id: int
    article_id: Optional[int] = None
    question: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    sentiment: SentimentBreakdown
    arguments: List[ArgumentResponse] = []

    class Config:
        from_attributes = True


class DebateRoomListItem(BaseModel):
    id: int
    question: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DebateSummaryResponse(BaseModel):
    support_summary: str
    oppose_summary: str
    common_ground: str


class ArgumentSubmitResult(BaseModel):
    argument: ArgumentResponse
    warning: Optional[str] = None
