from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from App.database.db import get_db
from App.models.promise import Promise
from App.models.user import User
from App.routes.auth import get_current_user, require_role
from App.schemas.promise import PromiseCreate, PromiseUpdate, PromiseResponse

router = APIRouter(prefix="/promises", tags=["Promise Tracker"])


@router.get("", response_model=list[PromiseResponse])
def list_promises(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Promise).filter(Promise.institution == current_user.institution).order_by(
        Promise.created_at.desc()).all()


@router.post("", response_model=PromiseResponse)
def create_promise(request: PromiseCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    promise = Promise(
        institution=current_user.institution, title=request.title, description=request.description,
        department=request.department, status=request.status,
        percent_complete=request.percent_complete, due_date=request.due_date
    )
    db.add(promise)
    db.commit()
    db.refresh(promise)
    return promise


@router.patch("/{promise_id}", response_model=PromiseResponse)
def update_promise(promise_id: int, request: PromiseUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    promise = db.query(Promise).filter(
        Promise.id == promise_id, Promise.institution == current_user.institution
    ).first()
    if not promise:
        raise HTTPException(status_code=404, detail="Promise not found")
    for field, value in request.dict(exclude_unset=True).items():
        setattr(promise, field, value)
    promise.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(promise)
    return promise


@router.delete("/{promise_id}")
def delete_promise(promise_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    promise = db.query(Promise).filter(
        Promise.id == promise_id, Promise.institution == current_user.institution
    ).first()
    if not promise:
        raise HTTPException(status_code=404, detail="Promise not found")
    db.delete(promise)
    db.commit()
    return {"message": "Promise deleted"}
