# GeoScope AI Architecture

## Overview
GeoScope AI follows a microservices-inspired monorepo architecture. 
- **Frontend**: React-based SPA that communicates via REST.
- **Backend API**: Python FastAPI application for routing and business logic.
- **Geospatial Engine**: PostGIS handles all spatial queries (intersections, buffers).
- **ML / AI Engine**: Vector embeddings via pgvector. Inference happens via local Python workers (offline models).
- **Storage**: S3-compatible blob storage (MinIO) for COG tiles and thumbnails.

## Diagram (Conceptual)
```
[ User Browser ]
       |
[ FastAPI Backend ]
  |      |      |
[DB]   [S3]   [ML Worker]
```
