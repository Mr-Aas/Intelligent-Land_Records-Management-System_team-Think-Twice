# CODING AGENT MASTER PROMPT
## AI-Enabled Urban Land Geospatial Integration System — Synthetic Prototype

You are the coding agent responsible for implementing a staged prototype of an AI-enabled urban land feature extraction, cadastral validation, and multi-department land-data integration system.

This document is the source of truth for the implementation.

IMPORTANT:
- Do NOT invent additional business rules.
- Do NOT change the workflow defined below.
- Do NOT skip stages.
- Do NOT connect to real government systems or assume real government files are available.
- For the current prototype, ALL source data must be synthetic.
- Build and TEST ONE STAGE AT A TIME.
- Do not implement later stages until the current stage is tested and accepted.
- If a technical detail is unspecified, choose the simplest reasonable implementation and clearly document the assumption rather than inventing a new business rule.
- Keep the architecture modular so synthetic data can later be replaced by real data without rewriting the core pipeline.

---

# 1. PROJECT PURPOSE

The eventual system will process current ground reality extracted from raster imagery, compare it with municipal building records, validate structures against cadastral land parcels, combine verified data with multiple government departments, resolve conflicting attributes, and provide a human-in-the-loop GIS interface for government officials.

The current goal is NOT to connect to real government data.

The current goal is to build a working prototype using:

1. A synthetic GeoTIFF representing NAKSHA-style raster input.
2. Synthetic Municipal Corporation / ULB building data.
3. Synthetic Bhu-Naksha / cadastral parcel data.
4. Synthetic Revenue Department data.
5. Synthetic Urban Local Body data.
6. Synthetic Urban Development Authority data.
7. Synthetic Registration & Stamps Department data.
8. Synthetic Directorate of Land Records / cadastral data.
9. Synthetic records designed specifically to exercise every workflow branch.

The system must later allow these synthetic sources to be replaced by real datasets.

---

# 2. FINAL BUSINESS WORKFLOW

The workflow is strictly sequential.

## SOURCE 1 — RASTER

Synthetic GeoTIFF represents current ground reality.

Pipeline:

Synthetic GeoTIFF
→ Rasterio reads raster
→ tile raster
→ GeoAI model
→ AI-extracted structures
→ structured GeoJSON

The AI-extracted dataset represents what physically exists according to the current imagery.

Call this dataset:

`ai_extracted`

Do not confuse this with official/legal registration data.

---

# 3. STAGE 0 — SYNTHETIC DATA GENERATION

Before processing the pipeline, create reproducible synthetic datasets.

Synthetic data must contain enough controlled examples to test EVERY important branch.

## 3.1 Synthetic GeoTIFF

Generate a small but spatially valid GeoTIFF.

Requirements:
- Use Rasterio.
- Give it a real CRS.
- Give it a valid affine transform.
- Give it known spatial bounds.
- Make the raster deterministic/reproducible.
- Include synthetic visual patterns representing buildings/structures.
- Keep its size small enough for local development.
- It must be possible to process it tile-by-tile exactly like a future massive GeoTIFF.

Do not fake GeoTIFF metadata after generation. The file must actually contain valid geospatial metadata.

## 3.2 Synthetic Municipal Data

Create synthetic municipal building records representing Meerut Nagar Nigam / ULB data.

The dataset must contain examples where:
- A building has no municipal match.
- A building has partial/minor overlap.
- A building has substantial overlap.
- Multiple synthetic records can be spatially compared.

The exact synthetic IDs and values are arbitrary, but they must be deterministic.

## 3.3 Synthetic Cadastral Data

Create synthetic Bhu-Naksha-style land parcels.

Each parcel needs a unique parcel identifier such as:

`parcel_id`

Include parcels specifically designed to test:
- structure completely inside one parcel;
- structure overflowing slightly beyond a parcel;
- structure overflowing beyond the configured threshold;
- structure associated with more than one parcel;
- disputed spatial relationships.

## 3.4 Other Department Data

Create synthetic records for:

- Revenue Department
- Urban Local Body / Municipal Corporation
- Urban Development Authority
- Registration and Stamps Department
- Directorate of Land Records / Cadastral System

These datasets must deliberately contain:
- matching attributes;
- missing attributes;
- conflicting attributes;
- different representations of the same field;
- enough data to test conflict resolution later.

Do not claim the synthetic values represent real government records.

---

# 4. STAGE 1 — GEOAI RASTER FEATURE EXTRACTION

Build and test this stage independently first.

## Input

Synthetic GeoTIFF.

## Processing

Use Rasterio to:

1. Open the GeoTIFF.
2. Read its CRS.
3. Read its affine transform.
4. Read raster dimensions.
5. Divide the raster into tiles.
6. Process tiles independently.
7. Preserve spatial position for every tile.

Use overlapping tiles where appropriate.

Default prototype tile size:

`1024 x 1024`

However, because the synthetic raster may be smaller than 1024×1024, the implementation must handle smaller dimensions correctly.

## GeoAI

The intended production model is:

`YOLOv11-seg`

The model is used for instance segmentation.

IMPORTANT:
- Do not silently substitute another model as the production choice.
- For the prototype, if a trained YOLOv11-seg model is not available, create a clearly isolated deterministic mock/inference adapter that produces synthetic detections.
- The mock must have the same output contract expected from the real model.
- Do NOT pretend the mock is a trained AI model.
- The model interface must later allow YOLOv11-seg to be plugged in without changing downstream geospatial logic.

## Output

Create:

`ai_extracted.geojson`

Each extracted structure must have:
- unique structure ID;
- geometry;
- class/type;
- source tile information if useful;
- confidence value if available;
- source/provenance indicating that it came from GeoAI;
- coordinate reference information through valid GeoJSON handling.

The geometry must be transformed from pixel coordinates into the GeoTIFF's spatial coordinates using Rasterio's transform.

Use Shapely for geometry construction and validation.

## Stage 1 acceptance test

Before moving forward, verify:

- GeoTIFF opens correctly.
- CRS is read correctly.
- tiles are generated correctly.
- all relevant tiles are processed.
- pixel coordinates become spatial coordinates correctly.
- output geometries are valid.
- duplicate detections caused by overlapping tiles are handled deterministically.
- GeoJSON is valid.
- every extracted structure has a stable ID.
- output can be loaded in QGIS or another GIS viewer.

STOP after this stage until it passes.

---

# 5. STAGE 2 — MUNICIPAL MATCHING

Input:

`ai_extracted`

and

synthetic Municipal Corporation / ULB building dataset.

This stage checks whether a physically detected structure has a corresponding municipal structure.

## IMPORTANT BUSINESS RULE

A municipal match does NOT require perfect geometric overlap.

If ANY meaningful spatial overlap exists between the AI-extracted structure and a municipal building record, the structure passes Stage 1.

Do NOT use complete containment here.

Do NOT classify a structure as fully legal merely because it overlaps municipal data.

The meaning of this stage is only:

"There is a municipal-recognized structure associated with this detected structure."

## Branch A — No municipal match

If no municipal building spatially overlaps the AI-extracted structure:

- status = `unregistered`
- save the structure and its currently available data.
- preserve the AI-extracted geometry.
- preserve relevant municipality-match information indicating no match.
- STOP processing this structure.
- Do NOT send it to cadastral validation.
- Do NOT send it to Stage 3.

## Branch B — Municipal overlap exists

If a municipal building overlaps the AI-extracted structure:

- the structure passes to the cadastral stage.
- preserve the municipal record reference.
- preserve relevant municipal fields.

Do NOT require perfect alignment.

## Stage 2 acceptance test

Synthetic test data MUST demonstrate:
- at least one `unregistered` structure;
- at least one structure that passes because of partial/minor overlap;
- deterministic results;
- no unregistered structure enters the cadastral stage.

STOP and test before proceeding.

---

# 6. STAGE 3 — CADASTRAL / BHU-NAKSHA VALIDATION

Input:

Only structures that passed municipal matching.

Data source:

Synthetic Directorate of Land Records / Survey Department / Bhu-Naksha cadastral parcel data.

The purpose is to determine whether the AI-extracted structure is completely within the cadastral land parcel on which it lies.

Use Shapely spatial operations.

## CASE A — STRUCTURE COMPLETELY WITHIN PARCEL

If the structure is completely within its relevant land parcel:

- status = `verified`
- attach/enrich relevant cadastral fields;
- preserve parcel ID;
- preserve provenance;
- send this record to Stage 4 / multi-department data integration.

## CASE B — STRUCTURE OVERFLOWS PARCEL

If the structure is not completely within one parcel, calculate the overflow according to the project's configured threshold logic.

The threshold MUST be configurable.

Do not hard-code unexplained business values into the code.

The implementation must clearly document what geometric measurement is being compared with the threshold.

## Threshold classification

### Condition 1

Overflow < threshold

→ `verified`

→ enrich with cadastral fields

→ send to Stage 4.

### Condition 2

Overflow >= threshold AND overflow < 2 × threshold

→ `audit_pending`

→ save the record

→ save a clear reason

→ example reason format:

`Overflow between parcel A and parcel B exceeds the verification threshold but remains below 2x threshold.`

→ DO NOT send to Stage 4 automatically.

→ send to human verification workflow.

### Condition 3

Overflow >= 2 × threshold

→ `disputed`

→ save the record

→ save a clear reason identifying the involved parcel(s)

→ DO NOT send to Stage 4 automatically.

→ send to human verification workflow.

IMPORTANT:

Both `audit_pending` AND `disputed` go to HUMAN VERIFICATION.

Neither automatically enters the multi-department Stage 4 pipeline.

Only `verified` records from this stage automatically proceed to Stage 4.

---

# 7. STAGE 3 DATA MODEL REQUIREMENTS

At minimum, preserve:

- structure_id
- geometry
- status
- parcel_id
- related_parcel_ids
- overflow_measure
- configured_threshold
- reason
- municipality_reference
- source/provenance
- verification_method

Possible verification_method values include:

- `geoai`
- `human`

For records automatically verified by the GeoAI/geospatial pipeline:

`verification_method = "geoai"`

Do not remove original source information when enriching the record.

---

# 8. HUMAN VERIFICATION WORKFLOW

This workflow applies to:

- `audit_pending`
- `disputed`

The records remain stored with their current status and reason.

They are exposed to a government-official frontend.

The target user is a:

`Lekhpal / Parvari`

## Authentication

Officials authenticate using an ID/password mechanism.

Do not integrate with a real government identity system in this prototype.

Use synthetic users.

## Tehsil filtering

Each synthetic official must be associated with a synthetic tehsil.

After login, the official sees records belonging to their assigned tehsil.

Do not expose all records to every official.

## GIS visualization

The official must be able to view:

- AI-extracted structure;
- cadastral parcel boundaries;
- relevant neighboring parcel(s);
- relevant spatial information.

The experience should be GIS-like, comparable conceptually to viewing/editing spatial data in QGIS.

The frontend technology should use the selected project stack:

- React
- Leaflet and/or MapLibre GL JS

Do not introduce a completely different frontend mapping stack without explicit approval.

## Human actions

Provide exactly these core decision actions:

### Mark Verified

Changes the record status to:

`verified`

Records:
- who performed the action;
- official/user ID;
- timestamp;
- previous status;
- new status.

Once verified by the official, the record becomes eligible for the Stage 4 pipeline.

### Locked Disputed

Changes the record status to:

`locked_disputed`

Records:
- who performed the action;
- official/user ID;
- timestamp;
- previous status;
- new status.

A locked disputed record does not automatically proceed to Stage 4.

Do not invent additional legal powers or workflows for the official.

---

# 9. STAGE 4 — MULTI-DEPARTMENT DATA INTEGRATION

Only records with an eligible `verified` status enter this stage.

The input consists of:

1. Prefinal verified spatial data.
2. Revenue Department data.
3. Urban Local Body / Municipal Corporation data.
4. Urban Development Authority data.
5. Registration and Stamps Department data.
6. Directorate of Land Records / Cadastral System data.

The system must combine information relating to the same land parcel.

## Purpose

Resolve conflicts among departments for the same fields.

Examples of potential fields:

- parcel ID
- land area
- land-use/purpose
- ownership
- current owner
- structures within parcel
- building information
- registration information
- cadastral information
- municipal information
- development-authority information
- relevant departmental identifiers
- provenance
- confidence/resolution metadata

Do NOT assume a fixed final schema is already known.

Design the schema to support extensible attributes.

## Conflict resolution

Build a clearly isolated smart-AI conflict-resolution component.

The component must:
- identify conflicting values;
- preserve source values;
- determine a resolved value;
- preserve which sources contributed;
- provide an explanation/reason for the resolution where possible;
- avoid silently deleting conflicting source information.

For the synthetic prototype, deterministic rules or a mock AI resolver may be used if an actual AI conflict-resolution model is not yet available.

Do NOT pretend a mock resolver is production AI.

The interface must later allow a real smart AI system to replace the mock resolver.

---

# 10. FINAL DATA — SINGLE SOURCE OF TRUTH

The Stage 4 output represents the consolidated parcel-level data.

Conceptually:

`one land parcel → one consolidated record`

This is the system's intended:

`Single Source of Truth`

It must retain provenance so that users can understand where important values originated.

Do not destroy the underlying departmental values.

The final record should support future updates and reprocessing.

---

# 11. UNREGISTERED BUILDING WORKFLOW

Structures classified as:

`unregistered`

at the municipal matching stage:

- remain stored;
- are NOT sent to cadastral validation;
- are NOT sent to Stage 4;
- are exposed/exported for municipal action.

The municipality can subsequently register/take action on those buildings.

When a future raster-processing cycle occurs and the municipal dataset has been updated, the newly registered building may then pass Stage 1.

This is an intended feedback loop.

Do not automatically change an unregistered record to registered without a new municipal data match.

---

# 12. DATABASE

Use:

`PostgreSQL + PostGIS`

for spatial data storage.

Use appropriate spatial geometry types and spatial indexes.

The database must be designed around the actual workflow states.

At minimum, preserve:
- source data;
- AI-extracted data;
- municipal matching result;
- cadastral validation result;
- audit/dispute state;
- human audit history;
- final consolidated data;
- provenance.

Do not flatten all source information into one table and lose lineage.

---

# 13. BACKEND

Use:

`FastAPI`

for the backend/API layer.

The backend must expose modular APIs for:

- ingestion;
- synthetic data generation where appropriate;
- GeoAI processing;
- municipal matching;
- cadastral validation;
- workflow status;
- human audit;
- authentication for synthetic officials;
- parcel retrieval;
- final consolidated data.

Do not build every operation into one giant endpoint.

Use service/module separation.

---

# 14. RASTER / GEOAI TOOLS

Use the selected tools:

- Rasterio
- Shapely
- YOLOv11-seg interface
- GeoJSON
- PostgreSQL
- PostGIS

For future scalability, preserve the architectural ability to use:

- Apache Airflow
- Apache Sedona
- AWS S3
- GeoServer

Do not force distributed infrastructure into the small synthetic prototype unless it is actually needed.

The prototype should remain runnable on a local development machine.

---

# 15. GIS SERVER

The selected GIS server is:

`GeoServer`

The architecture should allow PostGIS data to be served through GeoServer using standard geospatial services.

The exact service configuration can be implemented when the corresponding stage is reached.

Do not substitute a proprietary GIS server.

---

# 16. FRONTEND

Use:

`React`

For mapping, use:

- Leaflet
- and/or MapLibre GL JS

The government-review interface must prioritize:

- map visualization;
- parcel/structure inspection;
- status visibility;
- reason for audit/dispute;
- official decision actions;
- clear provenance.

Do not build unnecessary dashboards before the core workflow works.

---

# 17. WORKFLOW STATES

Use explicit status values.

At minimum:

`ai_extracted`

`unregistered`

`verified`

`audit_pending`

`disputed`

`locked_disputed`

Do not create arbitrary additional business statuses unless technically necessary. If one is technically necessary, document why.

Important transition rules:

```text
ai_extracted
      │
      ├── no municipal overlap ──→ unregistered
      │
      └── municipal overlap
                │
                ▼
          cadastral check
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
    verified  audit_pending  disputed
        │          │            │
        │          └────┬───────┘
        │               ▼
        │         human verification
        │               │
        │        ┌──────┴───────┐
        │        ▼              ▼
        │    verified    locked_disputed
        │        │
        └────────┘
             │
             ▼
       STAGE 4
```

`unregistered` does not proceed.

`audit_pending` does not automatically proceed.

`disputed` does not automatically proceed.

`locked_disputed` does not proceed.

Only eligible `verified` records proceed to Stage 4.

---

# 18. PROVENANCE

Every important transformation must preserve provenance.

The system should be able to answer:

- Where did this structure come from?
- Which raster/source produced it?
- Which municipal record matched it?
- Which parcel was used for validation?
- Why was it verified?
- Why was it marked audit_pending?
- Why was it disputed?
- Which official changed the status?
- Which departments contributed to the final field?
- Which value was selected when departments disagreed?

Do not discard original values merely because a resolved value exists.

---

# 19. SYNTHETIC DATA DESIGN PRINCIPLE

Synthetic data is not just placeholder data.

It must intentionally test the business workflow.

Create test cases for:

1. AI structure with no municipal record.
2. AI structure with small municipal overlap.
3. AI structure with strong municipal overlap.
4. AI structure fully inside one cadastral parcel.
5. AI structure with overflow below threshold.
6. AI structure with overflow at/above threshold but below 2× threshold.
7. AI structure with overflow at/above 2× threshold.
8. Structure involving two neighboring parcels.
9. Multiple structures inside one parcel.
10. Multiple department records for one parcel.
11. Department records containing conflicting values.
12. Missing departmental attributes.
13. Human official verifying an audit_pending record.
14. Human official locking a disputed record.
15. Verification provenance showing `geoai`.
16. Human decision provenance showing the official identity.

Use fixed random seeds so test results are reproducible.

---

# 20. TESTING STRATEGY

The project MUST be developed incrementally.

Do not implement everything and then test.

Required development cycle:

```text
IMPLEMENT STAGE
      ↓
RUN SYNTHETIC TESTS
      ↓
INSPECT OUTPUT
      ↓
VISUALIZE SPATIAL RESULT
      ↓
FIX PROBLEMS
      ↓
ACCEPT STAGE
      ↓
MOVE TO NEXT STAGE
```

Each stage must have:
- unit tests;
- integration tests where appropriate;
- sample output;
- clear pass/fail conditions.

Spatial outputs should be inspectable in QGIS.

---

# 21. RECOMMENDED DEVELOPMENT ORDER

Implement exactly in this order:

## Phase 1
Project structure + environment + configuration.

## Phase 2
Synthetic GeoTIFF generation + synthetic source datasets.

## Phase 3
Rasterio tiling pipeline.

## Phase 4
YOLOv11-seg adapter / deterministic prototype inference adapter.

## Phase 5
Pixel-to-spatial geometry conversion + `ai_extracted.geojson`.

## Phase 6
Municipal matching.

## Phase 7
Cadastral containment + threshold classification.

## Phase 8
PostGIS persistence and workflow-state management.

## Phase 9
Human verification backend.

## Phase 10
React GIS review frontend.

## Phase 11
Synthetic multi-department data integration.

## Phase 12
Conflict-resolution component.

## Phase 13
Final parcel-level Single Source of Truth.

## Phase 14
GeoServer integration.

## Phase 15
End-to-end testing.

Do not jump directly to Phase 15.

---

# 22. ENGINEERING RULES

1. Keep configuration separate from business logic.
2. Keep spatial operations separate from API routes.
3. Keep AI model inference behind an adapter/interface.
4. Keep synthetic data generation separate from production processing.
5. Use type hints where practical.
6. Validate all geometries.
7. Handle CRS explicitly.
8. Never silently mix coordinate reference systems.
9. Log important processing decisions.
10. Make pipeline runs reproducible.
11. Preserve source IDs.
12. Preserve provenance.
13. Use deterministic synthetic data.
14. Do not silently overwrite source records.
15. Make threshold values configurable.
16. Never invent real government APIs, schemas, credentials, or endpoints.
17. Never assume real NAKSHA, Bhu-Naksha, municipal, revenue, registration, or development-authority files are available.
18. Do not use real personal/land-owner information in the prototype.
19. Clearly label synthetic datasets.
20. Do not claim synthetic results represent real legal status.

---

# 23. ANTI-HALLUCINATION RULES FOR THE CODING AGENT

When information is missing:

- Do not invent government schemas.
- Do not invent government API endpoints.
- Do not invent authentication systems.
- Do not invent legal rules.
- Do not invent cadastral field definitions as authoritative.
- Do not claim a spatial rule is legally valid.
- Do not replace the defined workflow with a "better" workflow.
- Do not add automatic legal/illegal classification.
- Do not interpret `unregistered` as legally illegal.
- Do not interpret `verified` as a legal judgment unless explicitly defined by a future requirement.
- Do not send `audit_pending` or `disputed` records to Stage 4 automatically.
- Do not send `unregistered` records to Stage 4.
- Do not send `locked_disputed` records to Stage 4.

If a missing technical detail is required to continue:
1. identify it;
2. choose the minimum technical assumption needed;
3. isolate that assumption in configuration/code;
4. document it;
5. continue without changing the business workflow.

---

# 24. IMPORTANT DISTINCTION

The system has three different concepts that must never be conflated:

### CURRENT GROUND REALITY

`ai_extracted`

What GeoAI detects from the raster.

### GOVERNMENT SOURCE RECORDS

Municipal, cadastral, revenue, registration, development-authority, etc.

These are source datasets.

### CONSOLIDATED PARCEL TRUTH

The Stage 4 resolved record.

This is the system's intended parcel-level Single Source of Truth.

Never treat one of these as automatically equivalent to another.

---

# 25. FIRST TASK FOR THE CODING AGENT

DO NOT build the entire application immediately.

Start with ONLY:

1. Project structure.
2. Configuration system.
3. Synthetic GeoTIFF generator.
4. Synthetic municipal dataset generator.
5. Synthetic cadastral dataset generator.
6. Synthetic other-department dataset generators.
7. Basic dataset documentation.
8. Tests proving that the synthetic data was generated correctly.

Then STOP.

Report:
- files created;
- what each file does;
- how to run the synthetic-data generator;
- what datasets were produced;
- spatial CRS and bounds;
- test results;
- any assumptions made.

Do not implement Stage 1 until this initial synthetic-data stage is working and accepted.

---

# FINAL DIRECTIVE

Treat this document as the authoritative implementation specification.

The user has deliberately chosen this workflow based on their use case and currently available data.

Your job is to IMPLEMENT the workflow, not redesign it.

When a future real dataset becomes available, replace the corresponding synthetic adapter/input while preserving the established processing logic wherever possible.

Always build, test, inspect, and accept one stage before moving to the next.

---

# LOCKED DECISIONS (user, 2026-09-11)

These override earlier “ask later” notes. They do not add extra workflow stages.

1. **Municipal “meaningful” overlap:** any intersection counts, including when only edges/boundaries of an `ai_extracted` structure overlap a municipal building.
2. **Overflow metric:** not chosen yet. Do not implement a specific overflow measure or numeric threshold until a later decision. Keep the hook configurable.
3. **Primary parcel:** the cadastral parcel that contains the **major part** of the structure (largest intersection area) supplies `parcel_id`. Other overlapping parcels are related, not primary. Deterministic tie-break if needed: smaller `parcel_id`.
4. **Frontend:** skip for now. Implement **backend/server only**.
