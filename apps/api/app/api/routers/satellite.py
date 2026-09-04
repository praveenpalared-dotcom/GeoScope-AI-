from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from pathlib import Path
import os
import uuid

from app.db.session import get_db
from app.services.satellite_stac import satellite_stac_service
from app.services.ingestion import IngestionService

router = APIRouter(
    prefix="/satellite",
    tags=["Satellite Imaging"]
)

class SearchRequest(BaseModel):
    bbox: List[float]
    start_date: str
    end_date: str
    max_cloud_cover: float = 20.0
    limit: int = 10

class IngestRequest(BaseModel):
    item_id: str
    bbox: List[float]

@router.post("/search")
def search_satellite(request: SearchRequest):
    try:
        results = satellite_stac_service.search_scenes(
            bbox=request.bbox,
            start_date=request.start_date,
            end_date=request.end_date,
            max_cloud_cover=request.max_cloud_cover,
            limit=request.limit
        )
        return {
            "status": "success",
            "source": "Earth Search STAC",
            "collection": "sentinel-2-c1-l2a",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
def ingest_satellite(request: IngestRequest, db: Session = Depends(get_db)):
    try:
        # 1. Prepare temporary output path
        output_dir = Path("data/raw/sentinel2")
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_filename = f"{request.item_id}_{uuid.uuid4().hex[:6]}.tif"
        output_path = str(output_dir / temp_filename)
        
        # 2. Download the GeoTIFF
        download_result = satellite_stac_service.download_rgb(
            item_id=request.item_id,
            bbox=request.bbox,
            output_path=output_path
        )
        
        # 3. Process the file using existing ingestion logic
        ingestion_service = IngestionService(db)
        ingestion_result = ingestion_service.process_file(output_path)
        
        # Optionally clean up the temp file after processing to save space
        if os.path.exists(output_path):
            os.remove(output_path)
            
        return {
            "satellite_download": download_result,
            "ingestion_result": ingestion_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from sqlalchemy import func, desc
from app.models.geospatial import SatelliteScene, SatelliteTile

@router.get("/scenes/{scene_id}/tiles")
def get_scene_tiles(scene_id: str, db: Session = Depends(get_db)):
    try:
        # Use PostGIS functions to get WGS84 bounds
        tiles = db.query(
            SatelliteTile.id,
            SatelliteTile.scene_id,
            func.ST_XMin(func.ST_Envelope(SatelliteTile.geom)).label("west"),
            func.ST_YMin(func.ST_Envelope(SatelliteTile.geom)).label("south"),
            func.ST_XMax(func.ST_Envelope(SatelliteTile.geom)).label("east"),
            func.ST_YMax(func.ST_Envelope(SatelliteTile.geom)).label("north")
        ).filter(SatelliteTile.scene_id == scene_id).all()

        results = []
        for t in tiles:
            results.append({
                "id": t.id,
                "scene_id": t.scene_id,
                "image_url": f"http://localhost:8000/tiles/{t.scene_id}/{t.id}.png",
                "bounds": {
                    "west": t.west,
                    "south": t.south,
                    "east": t.east,
                    "north": t.north
                }
            })
            
        return {
            "status": "success",
            "scene_id": scene_id,
            "tiles": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest")
def get_latest_scene(db: Session = Depends(get_db)):
    try:
        latest_scene = db.query(SatelliteScene).order_by(desc(SatelliteScene.acquisition_time)).first()
        
        if not latest_scene:
            return {
                "status": "success",
                "scene": None
            }
            
        # Get tiles with bounds
        tiles = db.query(
            SatelliteTile.id,
            SatelliteTile.scene_id,
            func.ST_XMin(func.ST_Envelope(SatelliteTile.geom)).label("west"),
            func.ST_YMin(func.ST_Envelope(SatelliteTile.geom)).label("south"),
            func.ST_XMax(func.ST_Envelope(SatelliteTile.geom)).label("east"),
            func.ST_YMax(func.ST_Envelope(SatelliteTile.geom)).label("north")
        ).filter(SatelliteTile.scene_id == latest_scene.id).all()

        tile_results = []
        for t in tiles:
            tile_results.append({
                "id": t.id,
                "scene_id": t.scene_id,
                "image_url": f"http://localhost:8000/tiles/{t.scene_id}/{t.id}.png",
                "bounds": {
                    "west": t.west,
                    "south": t.south,
                    "east": t.east,
                    "north": t.north
                }
            })
            
        return {
            "status": "success",
            "scene": {
                "id": latest_scene.id,
                "acquisition_time": latest_scene.acquisition_time.isoformat() if latest_scene.acquisition_time else None,
                "cloud_cover": latest_scene.cloud_cover,
                "platform": latest_scene.platform,
                "tiles": tile_results
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
