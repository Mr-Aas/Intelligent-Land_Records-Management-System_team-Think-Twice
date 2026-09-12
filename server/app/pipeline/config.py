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

GEOTIFF_INPUT_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic" / "synthetic_raster.tif")
AI_EXTRACTED_OUTPUT_PATH: str = str(_PROJECT_ROOT / "data" / "output" / "ai_extracted.geojson")
MUNICIPAL_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic" / "municipal_buildings.geojson")
CADASTRAL_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic" / "cadastral_parcels.geojson")

# Department data paths (Stage 4 — placeholders)
REVENUE_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic" / "revenue_dept.geojson")
ULB_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic" / "ulb_data.geojson")
UDA_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic" / "uda_data.geojson")
REGISTRATION_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic" / "registration_stamps.geojson")
DLR_DATA_PATH: str = str(_PROJECT_ROOT / "data" / "synthetic" / "directorate_land_records.geojson")

# ---------------------------------------------------------------------------
# Stage 1 — Raster tiling
# ---------------------------------------------------------------------------
TILE_SIZE: int = 1024       # pixels (width & height)
TILE_OVERLAP: int = 64      # pixels of overlap per tile edge

# ---------------------------------------------------------------------------
# Coordinate Reference System
# ---------------------------------------------------------------------------
# EPSG:32643 = UTM Zone 43N — covers Meerut / western-UP pilot area.
DEFAULT_CRS_EPSG: int = 32643

# ---------------------------------------------------------------------------
# Stage 1 — Inference adapter
# ---------------------------------------------------------------------------
USE_MOCK_INFERENCE: bool = True   # False → real YOLOv11-seg adapter
MOCK_RANDOM_SEED: int = 42       # deterministic synthetic detections

# Deduplication: IoU threshold for merging detections from overlapping tiles
DEDUP_IOU_THRESHOLD: float = 0.5

# ---------------------------------------------------------------------------
# Stage 3 — Cadastral validation (PLACEHOLDERS — metric TBD by user)
# ---------------------------------------------------------------------------
OVERFLOW_THRESHOLD = None   # numeric value TBD
OVERFLOW_METRIC = None      # measurement method TBD ("area_ratio", "hausdorff", …)
