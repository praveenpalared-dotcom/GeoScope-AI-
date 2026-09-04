# GeoScope AI — MASTER PLAN

**SIH26227 — Semantic Retrieval and Multi-Temporal Change Analysis of Satellite Imagery**

## 1. Vision
GeoScope AI is a production-grade, offline-capable geospatial intelligence platform for semantic search and multi-temporal change detection over satellite imagery. The system prioritizes correctness, precision, and analyst workflow, ensuring all requirements from the MoD (DGIS) problem statement are met securely and reproducibly.

## 2. Architecture Overview
- **Frontend (Web):** React, TypeScript, Vite, Tailwind CSS, shadcn/ui, MapLibre GL JS, Recharts, Lucide icons.
- **Backend (API):** Python, FastAPI, Pydantic, SQLAlchemy, Uvicorn, Celery (or FastAPI background tasks).
- **Database:** PostgreSQL with PostGIS (geospatial operations) and pgvector (embeddings).
- **Object Storage:** S3-compatible (MinIO for local development).
- **Geospatial Processing:** GDAL, Rasterio, GeoPandas, Shapely, PyProj.
- **Machine Learning Engine:** Open foundation models (CLIP/SigLIP) for semantic search, baseline Siamese/U-Net models for change detection, clustering (HDBSCAN/K-Means) for discovery. All running offline.
- **Infrastructure:** Docker and Docker Compose for reproducible, offline-ready deployment.

## 3. Database Schema (PostgreSQL)
- **`users`**: Authentication and roles (Admin, Analyst).
- **`aoi`**: Saved Areas of Interest (polygons via PostGIS).
- **`satellite_sources`**: Registered satellite platforms (Sentinel-2, Landsat).
- **`satellite_scenes`**: Ingested scene metadata, bounding box (PostGIS geometry), acquisition time, processing status.
- **`satellite_tiles`**: Sub-scene tiles, associated COG paths, bounding box.
- **`embeddings`**: pgvector embeddings for tiles (for semantic and image-to-image retrieval).
- **`temporal_pairs`**: Defined before/after scene pairs for analysis.
- **`change_detections`**: Generated change masks from models (GeoJSON/polygons).
- **`change_objects`**: Specific classified changes (construction, deforestation).
- **`change_evidence`**: Evidence supporting earliest supported observation.
- **`clusters`**: Groupings of similar locations.
- **`analyst_reviews`**: Analyst feedback (CONFIRM, REJECT, ESCALATE) with audit trail.
- **`provenance_records`**: Tracking pipeline, model, and dataset versions used for each operation.
- **`model_versions` / `dataset_versions`**: Registries for reproducibility.

## 4. API Contracts
- `GET /health`, `GET /system/status`
- `POST /search/semantic` (Search by natural language)
- `POST /search/image` (Search by image)
- `GET /scenes`, `GET /tiles`
- `POST /temporal/analyze` (Trigger multi-temporal analysis)
- `POST /change-detection/run` (Trigger model inference)
- `GET /detections`, `GET /detections/{id}`
- `POST /detections/{id}/review` (Analyst decisions)
- `POST /discover/similar` (Clustering)
- `POST /geospatial/query` (PostGIS-backed spatial filters)
- `POST /reports/generate` (PDF/JSON/CSV export)
- `GET /evaluation` (Precision, Recall, metrics)
- `POST /ingestion/start` (Incremental ingestion pipeline)

## 5. Frontend Information Architecture
- **Dashboard:** High-level metrics, system status, active jobs.
- **Semantic Search:** Text/image input, map view, spatial filters.
- **Temporal Analysis:** Before/after view with swipe controls, timeline.
- **Change Detection:** Map layer toggles, confidence thresholds, change categories.
- **Review Queue:** Analyst-focused UI to confirm/reject/escalate detections.
- **Discover:** Clustering and similar site exploration map.
- **Reports:** Generation and download of evidence-backed reports.
- **Evaluation & System:** Hardware metrics, model metrics (precision, recall, latency), dataset metrics.

## 6. Development Milestones
- **MILESTONE 1 — Foundation:** App scaffold, React, FastAPI, PostgreSQL (PostGIS/pgvector), MinIO, Docker.
- **MILESTONE 2 — Satellite Ingestion:** Scene indexing, tiling, COG generation to MinIO, and metadata in Postgres.
- **MILESTONE 3 — Semantic Retrieval:** Offline embedding generation and vector search.
- **MILESTONE 4 — Image-to-Image Search:** Retrieve similar locations by image vector.
- **MILESTONE 5 — Temporal Engine:** Pairing scenes over time across AOIs.
- **MILESTONE 6 — Change Detection:** Run baseline change models and classify.
- **MILESTONE 7 — False-Alarm Suppression:** Registration, cloud/shadow checks, contextual validation.
- **MILESTONE 8 — Geospatial Reasoning:** Spatial intersections and buffers via PostGIS.
- **MILESTONE 9 — Clustering / Discovery:** Unsupervised grouping of similar detections.
- **MILESTONE 10 — Analyst Workflow:** Queue, review actions, and audit logs.
- **MILESTONE 11 — Provenance:** Complete tracking of models, pipelines, and scenes used.
- **MILESTONE 12 — Evaluation:** Precision/Recall scripts, timing metrics, evaluation report UI.
- **MILESTONE 13 — Reports:** Exporting evidence (PDF/JSON/GeoJSON).
- **MILESTONE 14 — Offline Mode:** Validating strict offline execution (no external API calls).
- **MILESTONE 15 — SIH Polish:** UI/UX refinement, performance, demo scenario orchestration.
