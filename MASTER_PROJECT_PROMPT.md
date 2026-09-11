# SUPERSEDED

This file is **not** the implementation specification.

Use [`CODING_AGENT_MASTER_PROMPT.md`](CODING_AGENT_MASTER_PROMPT.md) (copied from the current `prompt.md`). Do not implement GNSS star-topology, ULPIN traffic-light snapping, or SAM/YOLOv8 as the live pipeline.

The historical brief below is retained only as archive.

<!-- # MASTER BUILD BRIEF
## Project: AI-Enabled Geospatial Integration Platform for Urban Land Record Management
### Smart India Hackathon 2026 — Problem Statement No. 2013

---

## 0. HOW TO USE THIS DOCUMENT (read this first, agent)

You are being onboarded as the lead engineering agent for this project. This brief contains the full problem context, the architecture we have already decided on, and the exact technology stack we have committed to. **Nothing in Sections 1–8 is open for you to redesign or second-guess** — treat it as a fixed specification. Your job starts at Section 9 (Working Process Rules).

This is a **multi-week build**, not a single-shot generation task. You must not attempt to generate the entire system in one response. You will work in **phases** (defined in Section 11), and after completing each phase you must **stop, summarize what you built, flag any assumptions you made, and wait for explicit approval** before starting the next phase. If anything in this brief is ambiguous, ask a clarifying question before writing code rather than guessing.

---

## 1. PROBLEM CONTEXT (why this system needs to exist)

Urban land administration in India is fragmented across multiple departments that were never designed to interoperate:

- **State Revenue Department** (e.g., UP Bhulekh / Bhu-Naksha) — textual Record of Rights (Khatauni/Khasra), legacy paper-digitized cadastral maps, treated as the historical legal baseline for rural/agricultural parcels.
- **Stamp & Registration Department** (e.g., IGRSUP) — legal sale deed transactions.
- **Urban Local Bodies / Development Authorities** (Municipal Corporations, LDA, NOIDA, etc.) — property tax IDs, municipal building footprint maps, master layout plans.
- **Central Authorities** (NHAI Bhoomirashi, Railways REAMS, Defence Estates Raksha Bhoomi) — linear infrastructure corridors and large land banks.
- **NAKSHA/SVAMITVA drone survey programme** — modern high-precision Orthorectified Imagery (ORI), DSM/DTM, GNSS/CORS ground-truthed coordinates.

These sources disagree with each other in ways that are **not simple data-entry errors** but genuine structural conflicts:

- **Semantic mutation lag** — a sale deed is registered but never mutated in Revenue records, so ownership fields disagree across departments.
- **Temporal/physical drift** — legacy records show agricultural land; modern imagery shows roads or buildings now standing there.
- **Dimensionality mismatch** — 2D cadastral assumptions break down against 3D reality (multi-storey apartments, overhead utility lines, underground pipelines crossing a single 2D parcel).
- **Sliver polygons** — overlaying an old hand-digitized map on a modern high-resolution survey creates tiny false gaps/overlaps purely from scale/accuracy mismatch, not real boundary disputes.
- **Ground truth contradictions** — physical boundary walls visible in imagery may not match the legally recorded partition line.

The platform's job is to **automatically integrate, harmonize, validate, and synchronize** these sources into a single trustworthy record per parcel — without ever silently overwriting a citizen's legal boundary based on an algorithm's guess.

---

## 2. SELECTED APPROACH (fixed — do not deviate)

**Hybrid GeoAI Pipeline with Human-in-the-Loop Safe Mode.**

- Core backend automation runs on **GeoPandas + Shapely**, not manual desktop GIS tools. Desktop GIS (QGIS) is used only for our own testing/visual QA during development, never as a runtime dependency of the platform itself.
- The system **rejects blind automation**. It never merges or overwrites boundary data purely on confidence — it runs a strict **Confidence-Based Branching Workflow**: auto-heal what is provably just sensor/digitizing noise, and hard-lock anything that could be a real-world dispute for human arbitration.
- Guiding principle to enforce in every module you write: **fail safe, not silent.** If a module is uncertain, it must flag and stop, never guess and proceed.

---

## 3. LEGAL HIERARCHY OF TRUTH (deterministic, non-negotiable priority order)

When cross-departmental spatial layers conflict, resolve using this strict priority — never a mathematical "best guess" blend:

| Priority | Source | Nature |
|---|---|---|
| **1 (highest)** | Modern GNSS/CORS ground-truthed coordinates (NAKSHA programme) | Immutable spatial anchor |
| **2** | CV-extracted physical boundaries from Drone ORI (SAM / YOLOv8-seg outputs) | High-confidence but not immutable |
| **3 (lowest)** | Legacy digitized paper village maps (Bhu-Naksha) | Reference only, most error-prone |

**Snapping rule — Star Topology, not pairwise chaining:** Priority 1 is treated as a fixed, immutable anchor. Priority 2 and Priority 3 geometries are each independently evaluated and snapped directly against Priority 1. **Never chain snap (3→2→1)** — sequential chaining compounds error and causes map drift. This must be enforced architecturally, not left as a coding convention someone can accidentally violate.

---

## 4. THREE-STAGE AI ARCHITECTURE (the pipeline backbone)

```
[Ingestion Engine] → [Stage 1: Spatial/Vision Engine] → [Stage 2: Semantic/Text Engine] → [Stage 3: Confidence & Export Engine]
```

**Stage 1 — Spatial/Vision Engine (geometry phase)**
- Ingest Drone Imagery, ORI, DSM/DTM, existing CAD/cadastral vector layers, and the **zoning/land-use layer** from the Development Authority master plan (required input — see Section 5).
- Run CV/segmentation (SAM, YOLOv8-seg) to auto-extract building footprints and parcel outlines from raster imagery.
- Run coordinate transformation to a single working CRS (WGS84 / appropriate UTM zone — do not hardcode one zone; make this configurable per Area of Interest).
- Run automated topology correction using the Star Topology snapping rule (Section 3).

**Stage 2 — Semantic/Text Engine (attribute phase)**
- Run IoU-based spatial matching between layers to determine whether an AI-extracted boundary and a municipal/legacy boundary represent the same real-world parcel.
- Run entity resolution on text attributes (name variant normalization, e.g. "R. K. Sharma" vs "Ram Kumar"; unit conversion, e.g. Hectares ↔ Sq. Yards).
- Apply the Legal Hierarchy of Truth (Section 3) to resolve conflicting fields — never a statistical average or arbitrary tie-break.

**Stage 3 — Confidence & Export Engine**
- Produce one consolidated "Single Source of Truth" master record per unique parcel, keyed to a unified **14-digit ULPIN (Bhu-Aadhar)** identifier.
- Emit a breakdown Confidence Score (e.g., Boundary Accuracy %, Ownership Certainty %) rather than a single opaque number — each sub-score must be traceable to the specific data conflict that produced it.

---

## 5. BRANCHING LOGIC — THREE-TIER TRAFFIC LIGHT MODEL (exact thresholds, fixed)

Every extracted geometric anomaly (post sliver-extraction) is evaluated against a **zone-dependent distance threshold**, not a single flat number. This requires a **zoning/land-use classification layer as a mandatory Stage 1 input** — do not build any part of this logic assuming a flat threshold.

| Zone Type | Authority Source | Threshold | Rationale |
|---|---|---|---|
| Dense Urban / Commercial | Municipal built footprints | ≤ 10 cm | High land value; even a 15cm error risks bisecting a structural wall or apartment footprint |
| Suburban / Residential | Drone-extracted physical walls (SAM) | ≤ 15 cm | Standard tolerance for plastering/structural offsets |
| Agricultural / Peri-Urban | Legacy paper map (Bhu-Naksha) | ≤ 50 cm | Legacy scaling error is expected; deviation here is digitization skew, not land theft |

**Traffic-light branching (applies within whichever threshold band is active for the zone):**

- 🟢 **Green (within threshold)** — "Auto-Heal Engine": snap vertices programmatically, harmonize attributes, proceed silently to ULPIN generation. No human step.
- 🟡 **Amber (threshold to 2× threshold)** — "Review Needed / Lightweight Audit": tentatively merge the boundary to avoid transactional delay, but raise an **unalterable system flag** and route to an asynchronous offline audit queue. Explicitly decide and document, per deployment, whether a tentatively-merged Amber parcel is usable for downstream actions (e.g. tax billing) while pending audit — do not leave this undefined in code.
- 🔴 **Red (beyond 2× threshold)** — "Hard Lock / Dispute": freeze the ULPIN record immediately, block any automated merge, push the conflict to the Web-GIS dashboard for human arbitration.

**New parcel bypass rule:** If a parcel is a first-time NAKSHA digitization with **zero overlapping polygons and zero conflicting ownership text** across all ingested sources, it skips the entire conflict-validation branch, is recorded at 100% Automation Confidence, and proceeds directly to ULPIN generation.

---

## 6. ULPIN / PARCEL STATUS MODEL

Every parcel record must carry one of these statuses at all times, and status transitions must only happen through the branching logic above — never a manual field edit path outside of the arbitration workflow:

- `VERIFIED` — passed Green branch or new-parcel bypass; ULPIN generated.
- `AUDIT_PENDING` — Amber branch; tentatively merged, awaiting offline audit.
- `LOCKED_DISPUTE` — Red branch; ULPIN frozen, awaiting human arbitration via dashboard.

---

## 7. APPROVED TECHNOLOGY STACK (fixed — do not substitute without asking)

**Languages:** Python (backend, GIS, ML), JavaScript/TypeScript (frontend), SQL (spatial queries).

**Core GIS / geospatial libraries:** GDAL/OGR, GeoPandas, Shapely, Rasterio, PyProj, Fiona, PDAL.

**Spatial database:** PostgreSQL + PostGIS.

**AI / Computer Vision:** PyTorch, OpenCV, Segment Anything Model (SAM) for segmentation, YOLOv8-seg where object-detection-style extraction is more appropriate than full segmentation.

**Drone/photogrammetry:** OpenDroneMap (ODM) — open-source, scriptable; do not introduce Pix4D/Metashape (proprietary, not free).

**Backend framework:** FastAPI.

**Frontend:** React + Leaflet.js for the interactive Web-GIS dashboard.

**ETL/orchestration:** Apache Airflow.

**Desktop GIS (dev/QA only, not a runtime dependency):** QGIS.

**Cloud & infra:** AWS Free Tier, Docker.

**Do not introduce:** ArcGIS, Mapbox GL (paid tiers), FME, Pix4D/Metashape, Kubernetes, Kafka — all explicitly deprioritized for this build (either paid, or unnecessary complexity for current scope). If you believe one is genuinely needed later, flag it as a question rather than adding it silently.

---

## 8. EXISTING CODE — DO NOT REBUILD FROM SCRATCH

A first working module already exists for part of Stage 1/2: an IoU-based spatial matching + sliver polygon detection engine in GeoPandas/Shapely (`spatial_matching_engine.py`). I will paste or attach this file separately. Treat it as the **starting point** for the matching/sliver logic — refactor and extend it to match the exact Legal Hierarchy (Section 3) and Three-Tier Traffic Light thresholds (Section 5) rather than its current placeholder 85%/40% IoU cutoffs, which predate this finalized spec. Do not discard it and start over.

---

## 9. WORKING PROCESS RULES (how you must behave for this entire project)

1. **Work in phases, not one shot.** Follow the phase order in Section 11. Do not jump ahead to a later phase even if it seems easy to include now.
2. **Stop after every phase.** Summarize what was built, what assumptions you made, and any open questions — then wait for my explicit go-ahead before continuing.
3. **Ask before assuming.** If a requirement is ambiguous (a missing config value, an undefined edge case, a file format you weren't told about), ask a specific clarifying question rather than picking a default silently. Exception: trivial implementation details (variable naming, code style) don't need to be asked about.
4. **No fabricated data.** Never invent sample department data that pretends to be real government records. Use clearly-labeled synthetic/dummy test data for development and say so explicitly.
5. **Every module must state its assumptions in comments** — especially CRS/EPSG codes used, threshold values, and any place where you deviated from this brief because something was underspecified.
6. **Do not silently introduce new dependencies or tools** outside Section 7's list — ask first.
7. **Explainability over cleverness.** Since this system's outputs may be used to justify legal/administrative decisions, prefer simple, auditable logic over statistically elegant but opaque approaches, unless a phase explicitly calls for an ML model.
8. **Every merge/heal/lock decision must be logged** with enough detail (parcel ID, threshold used, zone type, distance measured, branch taken) to reconstruct why the system did what it did.

---

## 10. DEFINITION OF DONE (per phase)

A phase is not complete until:
- Code runs end-to-end on synthetic test data without errors.
- CRS handling is explicit and verified (no operation run on mismatched or undefined CRS).
- Edge cases from Section 1 (sliver polygons, invalid geometries, missing zoning layer, first-time parcel bypass) are handled, not just the happy path.
- A short written summary is provided back to me: what was built, key assumptions, what's still a stub/TODO for a later phase.

---

## 11. BUILD PHASES (execute strictly in this order; stop after each)

**Phase 0 — Environment & Scaffolding**
Set up the project repository structure, Python environment, dependency manifest (matching Section 7 exactly), and a basic README describing the architecture from Sections 2–6. No business logic yet. Propose a folder structure and wait for approval before generating files.

**Phase 1 — Data Ingestion & CRS Standardization**
Build the ingestion layer that accepts vector/raster inputs from multiple mock "department" sources, validates/repairs geometries, and standardizes CRS. Include the mandatory zoning/land-use layer as a first-class input, not an afterthought.

**Phase 2 — Spatial Matching & Sliver Resolution (Stage 1/2 core)**
Refactor the existing `spatial_matching_engine.py` to implement Star Topology anchoring (Section 3) and the zone-dependent Three-Tier Traffic Light thresholds (Section 5), replacing its placeholder thresholds.

**Phase 3 — Semantic/Attribute Engine (Stage 2)**
Entity resolution for text attributes (name normalization, unit conversion), and application of the Legal Hierarchy of Truth to resolve conflicting fields.

**Phase 4 — Confidence & Export Engine + ULPIN Generation (Stage 3)**
Consolidated master record generation, breakdown confidence scoring, ULPIN assignment logic including the new-parcel bypass rule.

**Phase 5 — PostGIS Schema & Status Model**
Relational schema implementing `VERIFIED` / `AUDIT_PENDING` / `LOCKED_DISPUTE` statuses, decision logs, and parcel history — designed before being implemented as raw SQL.

**Phase 6 — Backend API Layer (FastAPI)**
Expose ingestion, status query, and dashboard-facing endpoints over the pipeline built in Phases 1–5.

**Phase 7 — Web-GIS Dashboard (React + Leaflet)**
Visualize parcels by status (color-coded by traffic-light branch), and support the human arbitration workflow for `LOCKED_DISPUTE` and `AUDIT_PENDING` cases.

**Phase 8 — Orchestration & Deployment**
Airflow DAG wiring the pipeline stages together; Docker containerization; AWS Free Tier deployment configuration.

---

## 12. KICKOFF INSTRUCTION

Start with **Phase 0 only**. Before writing any files, ask me any clarifying questions you have about this brief, then propose a repository structure and wait for my approval before generating anything. -->
