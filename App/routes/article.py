from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArticleCreate(BaseModel):
    title: str
    category: Optional[str] = "general"
    lead: Optional[str] = None
    body: str
    image_url: Optional[str] = None
    status: Optional[str] = "draft"


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    lead: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None


class ArticleResponse(BaseModel):
    id: int
    author_id: int
    institution: str
    title: str
    category: str
    lead: Optional[str] = None
    body: str
    image_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True    class Config:
        from_attributes = True
