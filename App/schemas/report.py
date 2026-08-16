from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportCreate(BaseModel):
    description: str
    category: Optional[str] = None
    location: Optional[str] = None
    location_id: Optional[int] = None
    photo_url: Optional[str] = None
    anonymous: Optional[bool] = True


class ReportUpdateStatus(BaseModel):
    status: str
    assigned_department: Optional[str] = None
    official_response: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    institution: str
    description: str
    category: Optional[str] = None
    location: Optional[str] = None
    location_id: Optional[int] = None
    photo_url: Optional[str] = None
    status: str
    is_anonymous: int
    assigned_department: Optional[str] = None
    official_response: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
