from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SUGProfileCreate(BaseModel):
    name: str
    position: str
    term: Optional[str] = None
    photo_url: Optional[str] = None
    bio: Optional[str] = None


class SUGProfileResponse(BaseModel):
    id: int
    institution: str
    name: str
    position: str
    term: Optional[str] = None
    photo_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
