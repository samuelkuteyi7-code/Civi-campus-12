from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from App.database.db import get_db
from App.models.sug_profile import SUGProfile
from App.models.user import User
from App.routes.auth import get_current_user, require_role
from App.schemas.sug import SUGProfileCreate, SUGProfileResponse

router = APIRouter(prefix="/sug", tags=["SUG Profiles"])


@router.get("", response_model=list[SUGProfileResponse])
def list_sug_profiles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SUGProfile).filter(SUGProfile.institution == current_user.institution).all()


@router.post("", response_model=SUGProfileResponse)
def create_sug_profile(request: SUGProfileCreate, db: Session = Depends(get_db),
                        current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    profile = SUGProfile(
        institution=current_user.institution, name=request.name, position=request.position,
        term=request.term, photo_url=request.photo_url, bio=request.bio
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}")
def delete_sug_profile(profile_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    profile = db.query(SUGProfile).filter(
        SUGProfile.id == profile_id, SUGProfile.institution == current_user.institution
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()
    return {"message": "Profile deleted"}
