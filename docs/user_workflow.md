# GeoScope AI: End-to-End User Workflow & Architecture Plan

This document outlines the complete user journey for an analyst using the **GeoScope AI** platform. It details the step-by-step workflow, mapping user actions to the underlying APIs, agents (ML Workers), and infrastructure components.

---

## 1. Authentication & System Dashboard
**Goal:** Secure entry and high-level system overview.
* **User Action:** The analyst logs into the secure, offline-capable environment and views the dashboard. The dashboard displays system health, available satellite scenes, and pending review tasks.
* **API Calls:** 
  * `POST /auth/login` (Authentication)
  * `GET /health` & `GET /system/status` (Hardware/Metrics check)
* **Infrastructure:** 
  * **Database:** PostgreSQL (`users` table for RBAC - Admin/Analyst).
  * **Frontend:** React SPA (Vite) rendering system metrics via Recharts.

## 2. Area of Interest (AOI) Definition & Data Ingestion
**Goal:** Define target areas and process new raw satellite imagery.
* **User Action:** The analyst draws a polygon on the map to define an Area of Interest (AOI) or initiates an ingestion pipeline for new offline data disks containing Sentinel-2/Landsat imagery.
* **API Calls:**
  * `POST /geospatial/query` (Save and query AOI)
  * `POST /ingestion/start` (Trigger offline ingestion)
* **Agents / Workers:**
  * **Ingestion Pipeline Worker:** A background Celery/FastAPI task that reads raw imagery, tiles it into Cloud Optimized GeoTIFFs (COGs), and extracts metadata.
  * **Embedding Generator Agent:** Automatically generates vector embeddings for newly ingested tiles using open foundation models (e.g., CLIP/SigLIP).
* **Infrastructure:**
  * **Database:** PostgreSQL with PostGIS (`aoi`, `satellite_scenes`, `satellite_tiles`) and pgvector (`embeddings`).
  * **Storage:** MinIO (S3-compatible) for storing generated COGs and thumbnails.

## 3. Semantic & Image-based Retrieval
**Goal:** Quickly locate specific assets or terrain features.
* **User Action:** Instead of manually scanning massive areas, the analyst uses natural language (e.g., *"Find recently constructed military encampments"*) or uploads a reference image to search the database.
* **API Calls:**
  * `POST /search/semantic` (Text-based search)
  * `POST /search/image` (Image-based search)
* **Agents / Workers:**
  * **Retrieval Agent:** Intercepts the query, runs it through the local CLIP/SigLIP text/image encoder to generate a query vector, and performs a nearest-neighbor search in pgvector.
* **Infrastructure:**
  * **Database:** pgvector indexing for sub-second retrieval across millions of tiles.

## 4. Multi-Temporal Analysis Setup
**Goal:** Establish baseline and current state for change detection.
* **User Action:** The analyst selects an AOI and chooses two distinct timeframes (e.g., "Before: May 2023" and "After: May 2024"). The map updates with a swipe-control view comparing the two periods.
* **API Calls:**
  * `POST /temporal/analyze` (Defines the temporal pair)
  * `GET /scenes` & `GET /tiles` (Fetches the respective imagery)
* **Infrastructure:**
  * **Database:** PostgreSQL (`temporal_pairs`).
  * **Frontend:** MapLibre GL JS utilizing swipe and opacity layers to overlay COGs directly from MinIO.

## 5. Automated Change Detection Inference
**Goal:** Machine Learning driven identification of anomalies.
* **User Action:** The analyst triggers the change detection model over the selected temporal pair and sets confidence thresholds for specific classes (e.g., construction, deforestation).
* **API Calls:**
  * `POST /change-detection/run` (Initiate inference)
* **Agents / Workers:**
  * **ML Inference Worker:** A heavy offline Python process utilizing baseline Siamese/U-Net models. It reads the "before" and "after" COGs from MinIO, runs inference, and generates geospatial change masks.
  * **False-Alarm Suppression Agent:** Validates findings by cross-referencing clouds, shadows, and contextual anomalies to reduce false positives.
* **Infrastructure:**
  * **Database:** PostGIS (`change_detections` storing GeoJSON polygons).

## 6. Analyst Review Queue & Provenance
**Goal:** Human-in-the-loop verification and auditing.
* **User Action:** The ML-detected changes populate a "Review Queue". The analyst goes through each finding, zooming into the map, and marks the detection as `CONFIRM`, `REJECT`, or `ESCALATE`.
* **API Calls:**
  * `GET /detections` (Fetch queue)
  * `POST /detections/{id}/review` (Submit human decision)
* **Infrastructure:**
  * **Database:** PostgreSQL (`analyst_reviews`, `change_objects`).
  * **Provenance Tracking:** The `provenance_records` table logs which exact model version, dataset, and analyst were involved in the final decision, ensuring 100% reproducibility.

## 7. Discovery & Pattern Clustering
**Goal:** Uncover wider strategic patterns across the region.
* **User Action:** After confirming several specific changes (e.g., illegal logging camps), the analyst clicks "Find Similar Instances". 
* **API Calls:**
  * `POST /discover/similar`
* **Agents / Workers:**
  * **Clustering Agent:** Runs unsupervised algorithms (HDBSCAN/K-Means) over the confirmed detections and the embedding space to group similar undocumented changes across the entire database.
* **Infrastructure:**
  * **Database:** PostgreSQL (`clusters`).

## 8. Reporting and Evaluation
**Goal:** Export actionable intelligence for chain of command.
* **User Action:** The analyst generates an evidence-backed intelligence report. They can also view the model's performance metrics (Precision/Recall).
* **API Calls:**
  * `POST /reports/generate` (Generate PDF/GeoJSON)
  * `GET /evaluation` (System and ML metrics)
* **Infrastructure:**
  * **Backend:** FastAPI dynamically compiles the confirmed `change_evidence`, annotations, and spatial geometries into standard formats (PDF, CSV, GeoJSON) using offline templating engines.
