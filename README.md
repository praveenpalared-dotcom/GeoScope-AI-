# GeoScope AI

**SIH26227 — Semantic Retrieval and Multi-Temporal Change Analysis of Satellite Imagery**

GeoScope AI is a production-grade, offline-capable geospatial intelligence platform. 

## Features
- **Semantic Retrieval**: Natural language search over satellite imagery.
- **Multi-Temporal Change Analysis**: Compare scenes across time.
- **Change Detection**: ML models for identifying construction, deforestation, etc.
- **Analyst Workflow**: Review queue and provenance tracking.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js & npm
- Python 3.12+

### Running Infrastructure (PostgreSQL, PostGIS, pgvector, MinIO)
```bash
cd infrastructure
docker-compose up -d
```

### Running the Backend (FastAPI)
```bash
cd apps/api
python -m venv venv
# Activate venv
pip install -r requirements.txt
uvicorn main:app --reload
```

### Running the Frontend (React + Vite)
```bash
cd apps/web
npm install
npm run dev
```

For more details, see the `docs/` folder.
