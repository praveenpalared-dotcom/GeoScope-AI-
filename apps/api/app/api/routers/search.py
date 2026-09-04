from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.models.geospatial import SatelliteTile, SatelliteScene
from app.services.embeddings import embedding_service
from PIL import Image
import io

router = APIRouter(prefix="/search", tags=["search"])

class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 10
    bounding_box: Optional[List[float]] = None

class SearchResponseItem(BaseModel):
    id: str
    scene_id: str
    similarity_score: float
    minio_path: str
    geom: str
    image_url: str

class SearchResponse(BaseModel):
    results: List[SearchResponseItem]

@router.post("/semantic", response_model=SearchResponse)
def semantic_search(request: SemanticSearchRequest, db: Session = Depends(get_db)):
    """
    Perform a semantic search over satellite imagery using natural language.
    """
    try:
        vector = embedding_service.get_text_embedding(request.query)
        
        # Query pgvector for cosine similarity. In pgvector, cosine distance is `<=>`.
        # Cosine distance = 1 - Cosine similarity. So smaller distance = higher similarity.
        distance_expr = SatelliteTile.embedding.cosine_distance(vector)
        tiles_with_dist = db.query(SatelliteTile, distance_expr.label('distance')).order_by(distance_expr).limit(request.limit).all()
        
        results = []
        for tile, distance in tiles_with_dist:
            similarity = max(0.0, min(1.0, 1.0 - distance))
            results.append(SearchResponseItem(
                id=tile.id,
                scene_id=tile.scene_id,
                similarity_score=similarity,
                minio_path=tile.minio_path,
                geom=str(tile.geom), # WKT format
                image_url=f"http://localhost:8000/tiles/{tile.scene_id}/{tile.id}.png"
            ))
            
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image", response_model=SearchResponse)
def image_search(limit: int = 10, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Perform an image-to-image search to find similar geospatial features.
    """
    try:
        image_bytes = file.file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        vector = embedding_service.get_image_embedding(image)
        
        distance_expr = SatelliteTile.embedding.cosine_distance(vector)
        tiles_with_dist = db.query(SatelliteTile, distance_expr.label('distance')).order_by(distance_expr).limit(limit).all()
        
        results = []
        for tile, distance in tiles_with_dist:
            similarity = max(0.0, min(1.0, 1.0 - distance))
            results.append(SearchResponseItem(
                id=tile.id,
                scene_id=tile.scene_id,
                similarity_score=similarity, 
                minio_path=tile.minio_path,
                geom=str(tile.geom),
                image_url=f"http://localhost:8000/tiles/{tile.scene_id}/{tile.id}.png"
            ))
            
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
