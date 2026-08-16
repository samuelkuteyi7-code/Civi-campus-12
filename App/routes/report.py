from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from App.database.db import get_db
from App.models.report import Report
from App.models.user import User
from App.routes.auth import get_current_user, require_role
from App.schemas.report import ReportCreate, ReportUpdateStatus, ReportResponse

router = APIRouter(prefix="/reports", tags=["Issue Tracker"])


@router.post("", response_model=ReportResponse)
def submit_report(request: ReportCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    report = Report(
        user_id=current_user.id,
        institution=current_user.institution,
        description=request.description, category=request.category,
        location=request.location, photo_url=request.photo_url,
        is_anonymous=1 if request.anonymous else 0, status="submitted"
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=list[ReportResponse])
def list_reports(db: Session = Depends(get_db),
                  current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    return db.query(Report).filter(Report.institution == current_user.institution).order_by(
        Report.created_at.desc()).all()


@router.get("/mine", response_model=list[ReportResponse])
def my_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Report).filter(Report.user_id == current_user.id).order_by(
        Report.created_at.desc()).all()


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(
        Report.id == report_id, Report.institution == current_user.institution
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != current_user.id and current_user.role not in ("sug_officer", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view this report")
    return report


@router.patch("/{report_id}/status", response_model=ReportResponse)
def update_report_status(report_id: int, request: ReportUpdateStatus, db: Session = Depends(get_db),
                          current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    report = db.query(Report).filter(
        Report.id == report_id, Report.institution == current_user.institution
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = request.status
    if request.assigned_department:
        report.assigned_department = request.assigned_department
    if request.official_response:
        report.official_response = request.official_response
    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    return report
