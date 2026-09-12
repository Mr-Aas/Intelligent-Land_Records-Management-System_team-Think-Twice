<<<<<<< HEAD
# AI-Enabled Geospatial Integration Platform

Synthetic prototype for urban land feature extraction, cadastral validation, and multi-department integration (Smart India Hackathon 2026).

**Specification:** [`CODING_AGENT_MASTER_PROMPT.md`](CODING_AGENT_MASTER_PROMPT.md). The older GNSS/star-topology brief in `MASTER_PROJECT_PROMPT.md` is archived and not the live workflow.

## Architecture

Sequential pipeline on **synthetic** sources (replaceable later by real adapters):

1. **Stage 0 — Synthetic data:** GeoTIFF + municipal, cadastral, and other-department datasets.
2. **Stage 1 — GeoAI extraction:** Rasterio tiling → YOLOv11-seg adapter (or labeled mock) → `ai_extracted` GeoJSON.
3. **Stage 2 — Municipal matching:** any intersection with a ULB building (including edge-only) → `unregistered` (stop) or continue.
4. **Stage 3 — Cadastral validation:** containment vs overflow (metric TBD) vs a future configurable threshold → `verified` | `audit_pending` | `disputed`. Primary `parcel_id` is the parcel with the largest intersection area.
5. **Human verification (backend later):** Lekhpal/Parvari (tehsil-scoped) for audit/dispute → `verified` or `locked_disputed`. Frontend skipped for now.
6. **Stage 4 — Multi-department integration:** eligible `verified` records only → parcel-level Single Source of Truth with provenance.

Existing `server/app/engine` Stage 1/2 modules remain in the repo unused; the new pipeline will be added beside them. Current implementation focus is **server/backend only** (frontend skipped until requested).

## Tech Stack
- **Backend / geospatial:** Python, FastAPI, Rasterio, Shapely, GeoJSON, YOLOv11-seg (adapter).
- **Database / GIS:** PostgreSQL + PostGIS; GeoServer when that phase is reached.
- **Frontend:** deferred.
- **Local prototype:** Docker Compose PostGIS; do not require Airflow/Sedona/S3 until needed.
=======
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
>>>>>>> c06fd1b (Adding Frontend On it)
