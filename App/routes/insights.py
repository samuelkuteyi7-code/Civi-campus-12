from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import Counter

from App.database.db import get_db
from App.models.report import Report
from App.models.user import User
from App.routes.auth import get_current_user
from App.schemas.insights import InsightsResponse, CategoryBreakdown, ReportsOverTimePoint

router = APIRouter(prefix="/insights", tags=["Campus Insights"])


@router.get("", response_model=InsightsResponse)
def get_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reports = db.query(Report).filter(Report.institution == current_user.institution).all()

    total = len(reports)
    resolved = len([r for r in reports if r.status == "resolved"])
    in_progress = len([r for r in reports if r.status in ("assigned", "responded")])
    pending_verification = len([r for r in reports if r.status == "submitted"])

    category_counts = Counter(r.category or "Other" for r in reports)
    category_breakdown = [
        CategoryBreakdown(
            category=cat, count=count,
            percent=round(count / total * 100, 1) if total else 0
        )
        for cat, count in category_counts.most_common()
    ]

    cutoff = datetime.utcnow() - timedelta(weeks=8)
    recent_reports = [r for r in reports if r.created_at >= cutoff]
    week_counts = Counter()
    for r in recent_reports:
        week_start = r.created_at - timedelta(days=r.created_at.weekday())
        week_counts[week_start.strftime("%b %d")] += 1

    reports_over_time = [
        ReportsOverTimePoint(date=k, count=v)
        for k, v in sorted(week_counts.items(), key=lambda x: x[0])
    ]

    return InsightsResponse(
        total_reports=total, resolved=resolved, in_progress=in_progress,
        pending_verification=pending_verification,
        category_breakdown=category_breakdown, reports_over_time=reports_over_time
    )
