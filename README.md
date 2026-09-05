# AI-Enabled Geospatial Integration Platform

An automated, AI-driven platform for harmonizing conflicting urban land records across departments (Revenue, Municipal, and Drone Surveys). Built for Smart India Hackathon 2026 (Problem Statement 2013).

## Architecture

This project implements a **Hybrid GeoAI Pipeline with Human-in-the-Loop Safe Mode**.

### The 3-Stage Pipeline
1. **Stage 1 — Spatial/Vision Engine (Geometry Phase):** Ingests imagery and vectors, runs CV extraction (SAM/YOLOv8-seg), standardizes CRS, and applies star topology snapping to a GNSS-anchored source.
2. **Stage 2 — Semantic/Text Engine (Attribute Phase):** Performs IoU-based spatial matching to bind AI boundaries with legacy municipal ones, resolving textual disputes via Entity Resolution.
3. **Stage 3 — Confidence & Export Engine:** Produces a single verifiable ULPIN record based on zone-dependent thresholds.

### Branching Logic (Traffic Light Model)
Conflicts are evaluated against zone-dependent distance thresholds (e.g. 10cm for Urban, 50cm for Agricultural).
- 🟢 **Green (Auto-Heal):** Discrepancy within threshold. Programmatically snaps vertices and proceeds to ULPIN.
- 🟡 **Amber (Audit Pending):** Discrepancy up to 2× threshold. Tentatively merges but flags for offline audit.
- 🔴 **Red (Hard Lock):** Discrepancy > 2× threshold. Freezes parcel generation and routes to Web-GIS dashboard for human arbitration.

## Tech Stack
- **Backend/Data Science:** Python, FastAPI, GeoPandas, Shapely, PyTorch (SAM/YOLOv8-seg).
- **Frontend:** React, TypeScript, Leaflet.js, TailwindCSS.
- **Database:** PostgreSQL + PostGIS.
- **Orchestration:** Apache Airflow, Docker.
