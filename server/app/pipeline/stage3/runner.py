"""
runner — Orchestrator for Stage 3 (Cadastral / Bhu-Naksha Validation).

Workflow:
1. Ingests `stage2_municipal_matched.geojson` (structures passing municipal matching)
   and `bhu_naksha_parcels.geojson` (cadastral parcels).
2. Standardizes datasets to projected CRS (EPSG:32644).
3. Executes cadastral validation with configurable overflow threshold.
4. Exports:
   - `stage3_verified.geojson` (eligible to proceed to Stage 4 Multi-Department Integration)
   - `stage3_audit_pending.geojson` (routed to human verification workflow)
   - `stage3_disputed.geojson` (routed to human verification workflow)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.pipeline import config
from app.pipeline.stage2.matcher import load_layer_in_crs
from app.pipeline.stage3.validator import (
    CadastralValidatedRecord,
    validate_cadastral_dataset,
)

logger = logging.getLogger(__name__)


def export_cadastral_records_geojson(
    records: list[CadastralValidatedRecord],
    output_path: str | Path,
    crs_name: str = f"EPSG:{config.DEFAULT_CRS_EPSG}",
) -> Path:
    """Exports a list of CadastralValidatedRecord instances to GeoJSON."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    features = [r.to_geojson_feature() for r in records]
    feature_collection = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": crs_name},
        },
        "features": features,
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f, indent=2)

    logger.info("Exported %d records to %s", len(features), out)
    return out


def run_stage3(
    matched_structures_path: str = config.STAGE2_MATCHED_OUTPUT_PATH,
    cadastral_parcels_path: str = config.CADASTRAL_DATA_PATH,
    verified_output_path: str = config.STAGE3_VERIFIED_OUTPUT_PATH,
    audit_pending_output_path: str = config.STAGE3_AUDIT_PENDING_OUTPUT_PATH,
    disputed_output_path: str = config.STAGE3_DISPUTED_OUTPUT_PATH,
    threshold: float = config.OVERFLOW_THRESHOLD,
    target_epsg: int = config.DEFAULT_CRS_EPSG,
) -> tuple[Path, Path, Path, list[CadastralValidatedRecord], list[CadastralValidatedRecord], list[CadastralValidatedRecord]]:
    """Runs the complete Stage 3 Cadastral Validation pipeline.

    Returns:
        (verified_path, audit_pending_path, disputed_path, verified_list, audit_pending_list, disputed_list)
    """
    logger.info("Starting Stage 3 Cadastral Validation pipeline (threshold=%.2f m)...", threshold)

    # 1. Load layers projected in common working CRS
    matched_gdf = load_layer_in_crs(matched_structures_path, target_epsg=target_epsg)
    parcels_gdf = load_layer_in_crs(cadastral_parcels_path, target_epsg=target_epsg)

    logger.info(
        "Loaded %d municipal matched structures and %d cadastral parcels in EPSG:%d",
        len(matched_gdf), len(parcels_gdf), target_epsg,
    )

    # 2. Validate structures against cadastral parcels
    verified, audit_pending, disputed = validate_cadastral_dataset(
        matched_gdf=matched_gdf,
        parcels_gdf=parcels_gdf,
        threshold=threshold,
    )

    # 3. Export separate GeoJSON files for each branch
    v_path = export_cadastral_records_geojson(verified, verified_output_path, f"EPSG:{target_epsg}")
    a_path = export_cadastral_records_geojson(audit_pending, audit_pending_output_path, f"EPSG:{target_epsg}")
    d_path = export_cadastral_records_geojson(disputed, disputed_output_path, f"EPSG:{target_epsg}")

    logger.info("Stage 3 Cadastral Validation completed successfully.")
    return v_path, a_path, d_path, verified, audit_pending, disputed
