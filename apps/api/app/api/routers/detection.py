from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.detection import ChangeDetectionService
from app.models.geospatial import ChangeDetection, AnalystReview

router = APIRouter(prefix="/change-detection", tags=["change-detection"])

class ChangeDetectionRequest(BaseModel):
    pair_id: int

class ChangeDetectionResponse(BaseModel):
    status: str
    detections_made: int
    pair_id: int

class ReviewRequest(BaseModel):
    action: str # CONFIRM, REJECT, ESCALATE
    notes: str = ""

@router.post("/run", response_model=ChangeDetectionResponse)
def run_change_detection(request: ChangeDetectionRequest, db: Session = Depends(get_db)):
    """
    Trigger a baseline multi-temporal change detection pipeline.
    """
    try:
        service = ChangeDetectionService(db)
        result = service.baseline_change_detection(request.pair_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-ai", response_model=ChangeDetectionResponse)
def run_ai_change_detection(request: ChangeDetectionRequest, db: Session = Depends(get_db)):
    """
    Trigger an AI-powered multi-temporal change detection pipeline (BTC-B).
    """
    try:
        service = ChangeDetectionService(db)
        result = service.baseline_change_detection(request.pair_id, use_ai=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue")
def get_review_queue(db: Session = Depends(get_db)):
    """
    Fetch all pending detections for analyst review.
    """
    detections = db.query(ChangeDetection).filter(ChangeDetection.status == "pending").all()
    features = []
    for d in detections:
        features.append({
            "id": d.id,
            "pair_id": d.pair_id,
            "confidence": d.confidence,
            "classification": d.classification,
            "geom": str(d.geom)
        })
    return {"status": "success", "results": features}

@router.post("/detections/{id}/review")
def review_detection(id: int, req: ReviewRequest, db: Session = Depends(get_db)):
    """
    Submit an analyst review for a detection.
    """
    detection = db.query(ChangeDetection).filter(ChangeDetection.id == id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
        
    action = req.action.upper()
    if action not in ["CONFIRM", "REJECT", "ESCALATE"]:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    review = AnalystReview(
        detection_id=id,
        action=action,
        notes=req.notes
    )
    db.add(review)
    
    # Update detection status
    if action == "CONFIRM":
        detection.status = "confirmed"
    elif action == "REJECT":
        detection.status = "rejected"
    elif action == "ESCALATE":
        detection.status = "escalated"
        
    db.commit()
    return {"status": "success", "detection_id": id, "new_status": detection.status}

@router.get("/detections/{pair_id}")
def get_detection(pair_id: int, db: Session = Depends(get_db)):
    """
    Get the resulting change detection polygons for a specific pair.
    """
    detections = db.query(ChangeDetection).filter(ChangeDetection.pair_id == pair_id).all()
    
    features = []
    for d in detections:
        features.append({
            "id": d.id,
            "confidence": d.confidence,
            "classification": d.classification,
            "geom": str(d.geom) # WKT
        })
        
    return {
        "pair_id": pair_id,
        "status": "completed",
        "results": features
    }
