from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
import bcrypt
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta

from App.database.db import get_db
from App.models.user import User
from App.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from App.config.settings import JWT_SECRET
from App.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    except ValueError:
        return False


def create_jwt(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.replace("Bearer ", "")
    payload = decode_jwt(token)
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_role(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"This action requires one of these roles: {', '.join(allowed_roles)}")
        return current_user
    return role_checker


# 10/minute/IP — generous enough for real signups, tight enough to blunt
# mass fake-account creation scripts.
@router.post("/register", response_model=AuthResponse)
@limiter.limit("10/minute")
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=payload.name, email=payload.email,
        hashed_password=hash_password(payload.password),
        institution=payload.institution, department=payload.department,
        matric_number=payload.matric_number, role="student"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_jwt(new_user.id, new_user.email)
    new_user.token = token
    db.commit()

    return AuthResponse(
        name=new_user.name, email=new_user.email, institution=new_user.institution,
        role=new_user.role, token=token, message="Registration successful"
    )


# 5/minute/IP — the key brute-force defense. A password-guessing script
# gets throttled hard; a real user mistyping their password a few times
# is unaffected.
@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_jwt(user.id, user.email)
    user.token = token
    db.commit()

    return AuthResponse(
        name=user.name, email=user.email, institution=user.institution,
        role=user.role, token=token, message="Login successful"
    )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id, "name": current_user.name, "email": current_user.email,
        "institution": current_user.institution, "department": current_user.department,
        "role": current_user.role
    }
