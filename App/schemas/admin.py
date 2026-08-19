from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

Role = Literal["student", "sug_officer", "journalist", "admin"]
AssignableRole = Literal["student", "sug_officer", "journalist"]


class AdminUserItem(BaseModel):
    id: int
    name: str
    email: str
    institution: str
    department: Optional[str] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class RoleUpdateRequest(BaseModel):
    # Deliberately excludes "admin" — promoting a user to admin stays a
    # manual/SQL action, never exposed through the API. This means even a
    # compromised admin account can't mint more admins via this endpoint.
    role: AssignableRole
