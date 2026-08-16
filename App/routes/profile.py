from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from App.database.db import get_db
from App.models.user import User
from App.models.report import Report
from App.models.debate import DebateArgument
from App.routes.auth import get_current_user
from App.schemas.profile import ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/profile", tags=["Profile"])


def _to_response(db: Session, user: User) -> ProfileResponse:
    reports_count = db.query(Report).filter(Report.user_id == user.id).count()
    debates_count = db.query(DebateArgument.room_id).filter(
        DebateArgument.user_id == user.id
    ).distinct().count()
    return ProfileResponse(
        id=user.id, name=user.name, email=user.email, institution=user.institution,
        department=user.department, matric_number=user.matric_number, role=user.role,
        photo_url=user.photo_url, reports_submitted=reports_count, debates_joined=debates_count
    )


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _to_response(db, current_user)


@router.patch("", response_model=ProfileResponse)
def update_profile(request: ProfileUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    data = request.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return _to_response(db, current_user)
