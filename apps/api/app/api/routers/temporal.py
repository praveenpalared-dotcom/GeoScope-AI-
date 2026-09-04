from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.geospatial import SatelliteScene, TemporalPair
from pydantic import BaseModel

router = APIRouter(prefix="/temporal", tags=["temporal"])

class PairRequest(BaseModel):
    before_scene_id: str
    after_scene_id: str

@router.post("/pair")
def create_temporal_pair(req: PairRequest, db: Session = Depends(get_db)):
    """
    Find scenes that intersect spatially but were taken at different times,
    and create a TemporalPair record for them.
    """
    try:
        before = db.query(SatelliteScene).filter(SatelliteScene.id == req.before_scene_id).first()
        after = db.query(SatelliteScene).filter(SatelliteScene.id == req.after_scene_id).first()
        
        if not before or not after:
            raise HTTPException(status_code=404, detail="One or both scenes not found")
            
        if before.acquisition_time >= after.acquisition_time:
            raise HTTPException(status_code=400, detail="Before scene must be acquired before after scene")
            
        # Check intersection
        intersects = db.query(before.geom.ST_Intersects(after.geom)).scalar()
        if not intersects:
            raise HTTPException(status_code=400, detail="Scenes do not intersect spatially")
            
        # Check if pair already exists
        existing = db.query(TemporalPair).filter(
            TemporalPair.before_scene_id == before.id,
            TemporalPair.after_scene_id == after.id
        ).first()
        
        if existing:
            return {
                "status": "success", 
                "pair_id": existing.id, 
                "before_scene_id": before.id, 
                "after_scene_id": after.id
            }
            
        new_pair = TemporalPair(before_scene_id=before.id, after_scene_id=after.id)
        db.add(new_pair)
        db.commit()
        db.refresh(new_pair)
        
        return {
            "status": "success", 
            "pair_id": new_pair.id, 
            "before_scene_id": before.id, 
            "after_scene_id": after.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pair/{pair_id}")
def get_temporal_pair(pair_id: int, db: Session = Depends(get_db)):
    try:
        pair = db.query(TemporalPair).filter(TemporalPair.id == pair_id).first()
        if not pair:
            raise HTTPException(status_code=404, detail="Pair not found")
            
        return {
            "id": pair.id,
            "before_scene": {
                "id": pair.before_scene.id,
                "acquisition_time": pair.before_scene.acquisition_time,
                "platform": pair.before_scene.platform,
                "cloud_cover": pair.before_scene.cloud_cover
            },
            "after_scene": {
                "id": pair.after_scene.id,
                "acquisition_time": pair.after_scene.acquisition_time,
                "platform": pair.after_scene.platform,
                "cloud_cover": pair.after_scene.cloud_cover
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
