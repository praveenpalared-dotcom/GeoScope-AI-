from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.models.geospatial import SatelliteTile, ChangeDetection

router = APIRouter(prefix="/geospatial", tags=["geospatial"])

class GeospatialQueryRequest(BaseModel):
    wkt_polygon: str
    limit: int = 50

@router.post("/query")
def geospatial_query(request: GeospatialQueryRequest, db: Session = Depends(get_db)):
    """
    Find all satellite tiles and change detections that intersect a given Area of Interest (AOI).
    The AOI must be provided as a WKT polygon string.
    """
    try:
        aoi_geom = f"SRID=4326;{request.wkt_polygon}"
        
        # Find intersecting tiles
        tiles = db.query(SatelliteTile).filter(
            SatelliteTile.geom.ST_Intersects(aoi_geom)
        ).limit(request.limit).all()
        
        # Find intersecting change detections
        detections = db.query(ChangeDetection).filter(
            ChangeDetection.geom.ST_Intersects(aoi_geom)
        ).limit(request.limit).all()
        
        tile_results = [{"id": t.id, "scene_id": t.scene_id} for t in tiles]
        detection_results = [
            {"id": d.id, "pair_id": d.pair_id, "classification": d.classification} 
            for d in detections
        ]
        
        return {
            "status": "success",
            "intersecting_tiles": tile_results,
            "intersecting_detections": detection_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
