"""
Centralised configuration for the live pipeline.

All file paths are **placeholders** — replace them with real locations once
synthetic data is ready.  Every configurable value lives here so the rest
of the codebase never contains unexplained literals.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths  (PLACEHOLDERS — update when synthetic data is available)
# ---------------------------------------------------------------------------
# Root of the project (two levels up from this file: server/app/pipeline/)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

GEOTIFF_INPUT_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic_urban_land_department_data" / "indian.tif")
AI_EXTRACTED_OUTPUT_PATH: str = str(_PROJECT_ROOT / "data" / "outputs" / "ai_extracted.geojson")
MUNICIPAL_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic_urban_land_department_data" / "municipal_buildings.geojson")
CADASTRAL_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic_urban_land_department_data" / "bhu_naksha_parcels.geojson")

# Department data paths (Stage 4 — updated to point to synthetic_urban_land_department_data)
REVENUE_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic_urban_land_department_data" / "revenue_department.csv")
ULB_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic_urban_land_department_data" / "urban_local_body.csv")
UDA_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic_urban_land_department_data" / "urban_development_authority.csv")
REGISTRATION_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic_urban_land_department_data" / "registration_stamps.csv")
DLR_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic_urban_land_department_data" / "directorate_land_records.csv")

# Stage 2 — Municipal matching output paths
STAGE2_MATCHED_OUTPUT_PATH: str = str(_PROJECT_ROOT / "data" / "outputs" / "stage2_municipal_matched.geojson")
STAGE2_UNREGISTERED_OUTPUT_PATH: str = str(_PROJECT_ROOT / "data" / "outputs" / "stage2_unregistered.geojson")

# ---------------------------------------------------------------------------
# Stage 1 — Raster tiling
# ---------------------------------------------------------------------------
TILE_SIZE: int = 1024       # pixels (width & height)
TILE_OVERLAP: int = 64      # pixels of overlap per tile edge

# ---------------------------------------------------------------------------
# Coordinate Reference System
# ---------------------------------------------------------------------------
# EPSG:32644 = UTM Zone 44N — covers Haldwani / Kumaon Uttarakhand and synthetic dataset.
DEFAULT_CRS_EPSG: int = 32644

# ---------------------------------------------------------------------------
# Stage 1 — Inference adapter
# ---------------------------------------------------------------------------
USE_MOCK_INFERENCE: bool = False  # False → real YOLOv11-seg adapter
MOCK_RANDOM_SEED: int = 42       # deterministic synthetic detections

# Deduplication: IoU threshold for merging detections from overlapping tiles
DEDUP_IOU_THRESHOLD: float = 0.5

# ---------------------------------------------------------------------------
# Stage 3 — Cadastral validation (PLACEHOLDERS — metric TBD by user)
# ---------------------------------------------------------------------------
OVERFLOW_THRESHOLD = None   # numeric value TBD
OVERFLOW_METRIC = None      # measurement method TBD ("area_ratio", "hausdorff", …)

