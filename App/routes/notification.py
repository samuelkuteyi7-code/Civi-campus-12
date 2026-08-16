from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from App.database.db import get_db
from App.models.report import Report
from App.models.promise import Promise
from App.models.article import Article
from App.models.debate import DebateRoom, DebateArgument
from App.models.user import User
from App.routes.auth import get_current_user
from App.schemas.notification import NotificationItem

router = APIRouter(prefix="/notifications", tags=["Notifications"])

LOOKBACK_DAYS = 7


@router.get("", response_model=list[NotificationItem])
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cutoff = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    institution = current_user.institution
    notifications = []

    my_reports = db.query(Report).filter(
        Report.user_id == current_user.id, Report.updated_at >= cutoff
    ).order_by(Report.updated_at.desc()).all()
    for r in my_reports:
        if r.status == "assigned" and r.assigned_department:
            notifications.append(NotificationItem(
                type="report", title="Update on your report",
                message=f"Your reported issue has been assigned to {r.assigned_department}.",
                timestamp=r.updated_at.isoformat()
            ))
        elif r.status == "responded" and r.official_response:
            notifications.append(NotificationItem(
                type="report", title="Official response on your report",
                message=r.official_response[:120],
                timestamp=r.updated_at.isoformat()
            ))
        elif r.status == "resolved":
            notifications.append(NotificationItem(
                type="report", title="Your report was resolved",
                message="Your reported issue has been marked resolved.",
                timestamp=r.updated_at.isoformat()
            ))

    promises = db.query(Promise).filter(
        Promise.institution == institution, Promise.updated_at >= cutoff
    ).order_by(Promise.updated_at.desc()).limit(10).all()
    for p in promises:
        notifications.append(NotificationItem(
            type="promise", title="Promise update",
            message=f"\"{p.title}\" is now {p.percent_complete}% complete.",
            timestamp=p.updated_at.isoformat()
        ))

    articles = db.query(Article).filter(
        Article.institution == institution, Article.status == "published",
        Article.created_at >= cutoff
    ).order_by(Article.created_at.desc()).limit(10).all()
    for a in articles:
        notifications.append(NotificationItem(
            type="announcement", title="New announcement",
            message=a.title, timestamp=a.created_at.isoformat()
        ))

    rooms = db.query(DebateRoom).filter(
        DebateRoom.institution == institution, DebateRoom.status == "open"
    ).all()
    room_ids = [r.id for r in rooms]
    if room_ids:
        recent_args = db.query(DebateArgument).filter(
            DebateArgument.room_id.in_(room_ids), DebateArgument.created_at >= cutoff
        ).order_by(DebateArgument.created_at.desc()).limit(10).all()
        room_map = {r.id: r.question for r in rooms}
        for arg in recent_args:
            notifications.append(NotificationItem(
                type="debate", title="Debate update",
                message=f"New argument added in \"{room_map.get(arg.room_id, 'a debate')}\"",
                timestamp=arg.created_at.isoformat()
            ))

    notifications.sort(key=lambda n: n.timestamp, reverse=True)
    return notifications
