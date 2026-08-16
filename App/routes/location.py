from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from App.database.db import get_db
from App.models.location import CampusLocation
from App.models.report import Report
from App.models.user import User
from App.routes.auth import get_current_user, require_role
from App.schemas.location import LocationCreate, LocationResponse, MapLocationPoint

router = APIRouter(tags=["Campus Map"])


@router.post("/locations", response_model=LocationResponse)
def create_location(request: LocationCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    location = CampusLocation(
        institution=current_user.institution, name=request.name,
        latitude=request.latitude, longitude=request.longitude
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("/locations", response_model=list[LocationResponse])
def list_locations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CampusLocation).filter(CampusLocation.institution == current_user.institution).all()


@router.delete("/locations/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(require_role(["sug_officer", "admin"]))):
    location = db.query(CampusLocation).filter(
        CampusLocation.id == location_id, CampusLocation.institution == current_user.institution
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    db.delete(location)
    db.commit()
    return {"message": "Location deleted"}


@router.get("/map", response_model=list[MapLocationPoint])
def get_map(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    locations = db.query(CampusLocation).filter(CampusLocation.institution == current_user.institution).all()
    points = []
    for loc in locations:
        reports = db.query(Report).filter(Report.location_id == loc.id).all()
        total = len(reports)
        resolved = len([r for r in reports if r.status == "resolved"])
        in_progress = len([r for r in reports if r.status in ("assigned", "responded")])
        pending = len([r for r in reports if r.status == "submitted"])
        points.append(MapLocationPoint(
            location_id=loc.id, name=loc.name, latitude=loc.latitude, longitude=loc.longitude,
            total_reports=total, resolved=resolved, in_progress=in_progress, pending=pending
        ))
    return points
