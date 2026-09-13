"""
Master End-to-End Orchestration Script (§20, §21 of Master Prompt).

Executes the complete GIS AutoPilot processing pipeline in a single command:
Stage 0 (Data Gen) -> Stage 1 (GeoAI) -> Stage 2 (Municipal) -> Stage 3 (Cadastral)
  -> PostGIS Database Sync -> Stage 4 (Multi-Dept SSOT) -> GeoServer Publish.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# Add server directory to sys.path
_SERVER_DIR = Path(__file__).resolve().parents[1] / "server"
if str(_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVER_DIR))

from app.pipeline.stage1.runner import run_stage1
from app.pipeline.stage2.runner import run_stage2
from app.pipeline.stage3.runner import run_stage3
from app.pipeline.stage4.runner import run_stage4
from app.db.sync import sync_all_to_db
from app.geoserver.setup import setup_geoserver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("master_orchestrator")


def run_full_pipeline() -> dict:
    """
    Executes all pipeline stages sequentially and returns execution summary metrics.
    """
    start_time = time.time()
    logger.info("==================================================================")
    logger.info("   GIS AutoPilot — Master End-to-End Pipeline Execution Initiated   ")
    logger.info("==================================================================")

    results = {}

    # -------------------------------------------------------------------------
    # Step 1: Stage 0 Data Check
    # -------------------------------------------------------------------------
    logger.info("[Step 1/6] Verifying Stage 0 Synthetic Source Data...")
    t0 = time.time()
    from app.pipeline import config
    geotiff_exists = Path(config.GEOTIFF_INPUT_PATH).exists()
    cadastral_exists = Path(config.CADASTRAL_DATA_PATH).exists()
    results["stage0"] = {
        "geotiff_exists": geotiff_exists,
        "cadastral_exists": cadastral_exists,
        "duration_sec": round(time.time() - t0, 3),
    }

    # -------------------------------------------------------------------------
    # Step 2: Stage 1 GeoAI Raster Tiling & Feature Extraction
    # -------------------------------------------------------------------------
    logger.info("[Step 2/6] Executing Stage 1 GeoAI Raster Tiling & Feature Extraction...")
    t1 = time.time()
    ai_path, ai_structures = run_stage1()
    results["stage1"] = {
        "extracted_structures_count": len(ai_structures),
        "output_path": str(ai_path),
        "duration_sec": round(time.time() - t1, 3),
    }

    # -------------------------------------------------------------------------
    # Step 3: Stage 2 Municipal Matching
    # -------------------------------------------------------------------------
    logger.info("[Step 3/6] Executing Stage 2 Municipal Matching...")
    t2 = time.time()
    matched_path, unreg_path, matched, unreg = run_stage2()
    results["stage2"] = {
        "matched_count": len(matched),
        "unregistered_count": len(unreg),
        "matched_output": str(matched_path),
        "unregistered_output": str(unreg_path),
        "duration_sec": round(time.time() - t2, 3),
    }

    # -------------------------------------------------------------------------
    # Step 4: Stage 3 Cadastral Validation & Threshold Classification
    # -------------------------------------------------------------------------
    logger.info("[Step 4/6] Executing Stage 3 Cadastral Validation & Threshold Classification...")
    t3 = time.time()
    v_path, a_path, d_path, verified, audit_pending, disputed = run_stage3()
    results["stage3"] = {
        "verified_count": len(verified),
        "audit_pending_count": len(audit_pending),
        "disputed_count": len(disputed),
        "duration_sec": round(time.time() - t3, 3),
    }

    # -------------------------------------------------------------------------
    # Step 5: PostGIS Database Synchronization (§12)
    # -------------------------------------------------------------------------
    logger.info("[Step 5/6] Synchronizing Spatial Layers to PostgreSQL/PostGIS Database...")
    t4 = time.time()
    db_sync_res = sync_all_to_db()
    results["postgis_sync"] = {
        "status": db_sync_res.get("status"),
        "counts": db_sync_res.get("counts", {}),
        "duration_sec": round(time.time() - t4, 3),
    }

    # -------------------------------------------------------------------------
    # Step 6: Stage 4 Multi-Department Consolidation & Conflict Resolution
    # -------------------------------------------------------------------------
    logger.info("[Step 6/6] Executing Stage 4 Multi-Department SSOT Consolidation...")
    t5 = time.time()
    stage4_res = run_stage4()
    results["stage4"] = {
        "consolidated_parcels_count": stage4_res.get("count", 0),
        "conflicts_resolved_count": stage4_res.get("conflicts_resolved_count", 0),
        "duration_sec": round(time.time() - t5, 3),
    }

    # -------------------------------------------------------------------------
    # Step 7: GeoServer OGC Capabilities Publishing (§14, §15)
    # -------------------------------------------------------------------------
    logger.info("[Optional] Configuring GeoServer OGC WMS/WFS Layer Publishing...")
    gs_res = setup_geoserver()
    results["geoserver"] = {
        "status": gs_res.get("status"),
        "published_layers": gs_res.get("published_layers", []),
    }

    total_duration = round(time.time() - start_time, 3)
    results["total_execution_time_sec"] = total_duration

    logger.info("==================================================================")
    logger.info("   GIS AutoPilot — Master End-to-End Pipeline Execution SUCCESS   ")
    logger.info("   Total Time: %.3f seconds                                       ", total_duration)
    logger.info("   AI Extracted: %d | Matched: %d | Verified: %d | Disputed: %d    ",
                len(ai_structures), len(matched), len(verified), len(disputed))
    logger.info("   Stage 4 SSOT Parcels: %d                                       ", stage4_res.get("count", 0))
    logger.info("==================================================================")

    return results


if __name__ == "__main__":
    summary = run_full_pipeline()
    print("\n--- MASTER PIPELINE SUMMARY REPORT ---")
    import json
    print(json.dumps(summary, indent=2))
