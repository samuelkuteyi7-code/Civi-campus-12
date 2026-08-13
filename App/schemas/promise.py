from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PromiseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = "not_started"
    percent_complete: Optional[int] = 0
    due_date: Optional[str] = None


class PromiseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    percent_complete: Optional[int] = None
    due_date: Optional[str] = None


class PromiseResponse(BaseModel):
    id: int
    institution: str
    title: str
    description: Optional[str] = None
    department: Optional[str] = None
    status: str
    percent_complete: int
    due_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
