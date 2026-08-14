from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSendRequest(BaseModel):
    message: str


class ChatSendResponse(BaseModel):
    reply: str
