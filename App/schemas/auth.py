from pydantic import BaseModel
from typing import Optional


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    institution: str
    department: Optional[str] = None
    matric_number: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    name: str
    email: str
    institution: str
    role: str
    token: str
    message: str
