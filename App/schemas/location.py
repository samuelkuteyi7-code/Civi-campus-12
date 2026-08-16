from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class LocationCreate(BaseModel):
    name: str
    latitude: float
    longitude: float


class LocationResponse(BaseModel):
    id: int
    institution: str
    name: str
    latitude: float
    longitude: float
    created_at: datetime

    class Config:
        from_attributes = True


class MapLocationPoint(BaseModel):
    location_id: int
    name: str
    latitude: float
    longitude: float
    total_reports: int
    resolved: int
    in_progress: int
    pending: int
