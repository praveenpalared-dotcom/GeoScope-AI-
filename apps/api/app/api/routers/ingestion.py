from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.ingestion import IngestionService

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"],
)

class IngestionRequest(BaseModel):
    directory: str = "/data/raw"

@router.post("/start")
def start_ingestion(req: IngestionRequest, db: Session = Depends(get_db)):
    service = IngestionService(db)
    result = service.process_directory(req.directory)
    return result
