from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import routers
from app.api.routers import (
    search,
    detection,
    ingestion,
    temporal,
    geospatial,
    discovery,
    exports,
    tiles,
    auth,
    reports,
    satellite,
)

app = FastAPI(
    title="GeoScope AI API",
    description="Multi-modal satellite imagery retrieval and analytics platform",
    version="1.0.0"
)

# Setup SlowAPI Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(search.router)
app.include_router(detection.router)
app.include_router(ingestion.router)
app.include_router(temporal.router)
app.include_router(geospatial.router)
app.include_router(discovery.router)
app.include_router(exports.router)
app.include_router(tiles.router)
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(satellite.router)

@app.get("/health")
@limiter.limit("100/minute")
def health_check(request: Request):
    return {"status": "online", "version": "1.0.0"}

from app.db.session import engine
from sqlalchemy import text
from app.services.minio_client import minio_client
from fastapi.responses import RedirectResponse

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/system/status")
def system_status():
    db_status = "offline"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        pass
        
    minio_status = "offline"
    try:
        minio_client.list_buckets()
        minio_status = "online"
    except Exception:
        pass

    return {
        "status": "online" if db_status == "online" and minio_status == "online" else "degraded",
        "database": db_status, 
        "vector_store": db_status, # pgvector is in DB
        "object_storage": minio_status,
        "version": "0.1.0"
    }

from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.geospatial import SatelliteScene, ChangeDetection

@app.get("/dashboard/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    active_scenes_count = db.query(SatelliteScene).count()
    total_detections_count = db.query(ChangeDetection).count()
    pending_detections_count = db.query(ChangeDetection).filter(ChangeDetection.status == 'pending').count()
    
    return {
        "active_scenes": active_scenes_count,
        "active_scenes_trend": "Live updating",
        "change_detections": total_detections_count,
        "awaiting_review": pending_detections_count,
        "infrastructure_status": "Online",
        "infrastructure_detail": "All services running"
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
