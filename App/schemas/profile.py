from pydantic import BaseModel
from typing import Optional


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    photo_url: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    institution: str
    department: Optional[str] = None
    matric_number: Optional[str] = None
    role: str
    photo_url: Optional[str] = None
    reports_submitted: int
    debates_joined: int

    class Config:
        from_attributes = True
