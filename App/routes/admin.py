from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from App.database.db import get_db
from App.models.user import User
from App.routes.auth import require_role
from App.schemas.admin import AdminUserItem, RoleUpdateRequest

router = APIRouter(prefix="/admin", tags=["Admin"])


# All admin routes are scoped to the admin's own institution — an admin
# from one campus can never view or modify users on another campus, even
# if they somehow knew a user_id from elsewhere.
@router.get("/users", response_model=list[AdminUserItem])
def list_users(
    search: Optional[str] = Query(None, description="Match against name or email"),
    role: Optional[str] = Query(None, description="Filter by exact role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    query = db.query(User).filter(User.institution == current_user.institution)
    if role:
        query = query.filter(User.role == role)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
    return query.order_by(User.name).all()


@router.patch("/users/{user_id}/role", response_model=AdminUserItem)
def update_user_role(
    user_id: int,
    request: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't change your own role.")

    user = db.query(User).filter(
        User.id == user_id, User.institution == current_user.institution
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Admin status is untouchable through this endpoint in both directions:
    # you can't promote someone to admin (blocked at the schema level) and
    # you can't demote an existing admin either. Symmetry matters here —
    # without this check, one admin could demote every other admin down to
    # student, and there'd be no API path back since promotion stays
    # SQL-only. That would recreate the exact manual-SQL bottleneck this
    # feature was built to remove.
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Admin status can't be changed here. Contact a developer.")

    user.role = request.role
    db.commit()
    db.refresh(user)
    return user
