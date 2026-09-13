"""
runner — Orchestrator for Stage 2 (Municipal Matching).

Workflow:
1. Ingests `ai_extracted.geojson` (from Stage 1 / verified fixture) and `municipal_buildings.geojson`.
2. Standardizes datasets to projected CRS (EPSG:32644).
3. Executes spatial matching (`evaluate_municipal_matching`).
4. Exports:
   - `stage2_municipal_matched.geojson` (eligible for Stage 3 Cadastral Validation).
   - `stage2_unregistered.geojson` (retained for municipal registration workflow).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.pipeline import config
from app.pipeline.stage2.matcher import (
    MunicipalMatchedStructure,
    evaluate_municipal_matching,
    load_layer_in_crs,
)

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform

logger = logging.getLogger(__name__)


def export_structures_geojson(
    structures: list[MunicipalMatchedStructure],
    output_path: str | Path,
    crs_name: str = "urn:ogc:def:crs:OGC:1.3:CRS84",
) -> Path:
    """Exports a list of MunicipalMatchedStructure instances to WGS84 GeoJSON."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    transformer = Transformer.from_crs(f"EPSG:{config.DEFAULT_CRS_EPSG}", "EPSG:4326", always_xy=True)
    features = []
    for s in structures:
        feat = s.to_geojson_feature()
        geom = shape(feat["geometry"])
        wgs_geom = transform(transformer.transform, geom)
        feat["geometry"] = mapping(wgs_geom)
        features.append(feat)

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



def run_stage2(
    ai_extracted_path: str = config.AI_EXTRACTED_OUTPUT_PATH,
    municipal_data_path: str = config.MUNICIPAL_DATA_PATH,
    matched_output_path: str = config.STAGE2_MATCHED_OUTPUT_PATH,
    unregistered_output_path: str = config.STAGE2_UNREGISTERED_OUTPUT_PATH,
    target_epsg: int = config.DEFAULT_CRS_EPSG,
) -> tuple[Path, Path, list[MunicipalMatchedStructure], list[MunicipalMatchedStructure]]:
    """Runs the complete Stage 2 Municipal Matching pipeline.

    Returns:
        (matched_geojson_path, unregistered_geojson_path, matched_list, unregistered_list)
    """
    logger.info("Starting Stage 2 Municipal Matching pipeline...")

    # 1. Load layers projected in common working CRS
    ai_gdf = load_layer_in_crs(ai_extracted_path, target_epsg=target_epsg)
    mun_gdf = load_layer_in_crs(municipal_data_path, target_epsg=target_epsg)

    logger.info(
        "Loaded %d AI structures and %d municipal buildings in EPSG:%d",
        len(ai_gdf), len(mun_gdf), target_epsg,
    )

    # 2. Run matching
    matched, unregistered = evaluate_municipal_matching(ai_gdf, mun_gdf)

    # 3. Export outputs
    matched_path = export_structures_geojson(matched, matched_output_path, f"EPSG:{target_epsg}")
    unregistered_path = export_structures_geojson(unregistered, unregistered_output_path, f"EPSG:{target_epsg}")

    logger.info("Stage 2 Municipal Matching completed successfully.")
    return matched_path, unregistered_path, matched, unregistered
