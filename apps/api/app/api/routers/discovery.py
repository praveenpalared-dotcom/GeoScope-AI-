from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.discovery import DiscoveryService
from app.models.geospatial import DetectionCluster

router = APIRouter(prefix="/discover", tags=["discovery"])

@router.post("/cluster")
def cluster_detections(eps: float = 0.01, min_points: int = 2, db: Session = Depends(get_db)):
    """
    Run spatial clustering on all unclustered change detections to find hotspots.
    """
    try:
        service = DiscoveryService(db)
        result = service.generate_spatial_clusters(eps, min_points)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clusters")
def get_clusters(db: Session = Depends(get_db)):
    """
    Retrieve all detected spatial hotspots.
    """
    clusters = db.query(DetectionCluster).all()
    
    features = []
    for c in clusters:
        # Number of detections in this cluster
        det_count = len(c.detections)
        features.append({
            "id": c.id,
            "detection_count": det_count,
            "geom": str(c.geom)
        })
        
    return {
        "status": "success",
        "results": features
    }
