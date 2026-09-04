from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.models.geospatial import ChangeDetection, DetectionCluster
import shapely.wkt
import shapely.geometry

router = APIRouter(prefix="/exports", tags=["exports"])

def wkt_to_geojson_feature(wkt_str, properties):
    # Parse the WKT (ignoring SRID prefix if present)
    wkt_clean = wkt_str.replace("SRID=4326;", "") if wkt_str.startswith("SRID") else wkt_str
    try:
        geom = shapely.wkt.loads(wkt_clean)
        geom_dict = shapely.geometry.mapping(geom)
        return {
            "type": "Feature",
            "geometry": geom_dict,
            "properties": properties
        }
    except Exception as e:
        print(f"Failed to parse WKT: {e}")
        return None

@router.get("/detections")
def export_detections(db: Session = Depends(get_db)):
    """
    Export all confirmed detections as a GeoJSON FeatureCollection.
    """
    try:
        # For export, we usually want confirmed detections, but for MVP we can just export all non-rejected ones
        detections = db.query(ChangeDetection).filter(ChangeDetection.status != "rejected").all()
        
        features = []
        for d in detections:
            props = {
                "id": d.id,
                "confidence": d.confidence,
                "classification": d.classification,
                "status": d.status,
                "cluster_id": d.cluster_id,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            feature = wkt_to_geojson_feature(str(d.geom), props)
            if feature:
                features.append(feature)
                
        return JSONResponse(content={
            "type": "FeatureCollection",
            "features": features
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clusters")
def export_clusters(db: Session = Depends(get_db)):
    """
    Export all clusters as a GeoJSON FeatureCollection.
    """
    try:
        clusters = db.query(DetectionCluster).all()
        
        features = []
        for c in clusters:
            props = {
                "id": c.id,
                "detection_count": len(c.detections),
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            feature = wkt_to_geojson_feature(str(c.geom), props)
            if feature:
                features.append(feature)
                
        return JSONResponse(content={
            "type": "FeatureCollection",
            "features": features
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
