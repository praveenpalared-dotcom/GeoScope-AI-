from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.geospatial import SatelliteScene, ChangeDetection
from datetime import datetime, timedelta

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/detections/classification")
def get_detections_by_classification(db: Session = Depends(get_db)):
    try:
        results = db.query(ChangeDetection.classification, func.count(ChangeDetection.id)).group_by(ChangeDetection.classification).all()
        return [{"name": r[0].capitalize(), "value": r[1]} for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detections/status")
def get_detections_by_status(db: Session = Depends(get_db)):
    try:
        results = db.query(ChangeDetection.status, func.count(ChangeDetection.id)).group_by(ChangeDetection.status).all()
        return [{"name": r[0].capitalize(), "value": r[1]} for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scenes/timeline")
def get_scenes_timeline(db: Session = Depends(get_db)):
    try:
        # Get count of scenes by date for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        # Cast timestamp to date
        date_expr = func.date(SatelliteScene.acquisition_time)
        results = db.query(date_expr, func.count(SatelliteScene.id)).filter(SatelliteScene.acquisition_time >= thirty_days_ago).group_by(date_expr).order_by(date_expr).all()
        
        # Format for recharts: [{ date: '2023-10-01', count: 5 }, ...]
        return [{"date": r[0].strftime("%b %d"), "count": r[1]} for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
