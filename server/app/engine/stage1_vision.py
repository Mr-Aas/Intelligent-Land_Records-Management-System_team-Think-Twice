"""
Stage 1: Spatial/Vision Engine (Geometry Phase)
-----------------------------------------------
Orchestrates the ingestion of vector and raster layers, ensuring all
are reprojected to a common, dynamic CRS (e.g. EPSG:32643 for Meerut pilot).
Crucially, enforces the requirement for a zoning/land-use classification layer.
"""

from app.engine.ingestion import load_vector_layer, get_raster_metadata
from app.engine.crs_utils import DEFAULT_WORKING_CRS_EPSG
import logging

logger = logging.getLogger(__name__)

def run_stage1_ingestion(
    zoning_layer_path: str,
    ai_extracted_layer_path: str = None,
    legacy_cadastral_layer_path: str = None,
    target_epsg: int = DEFAULT_WORKING_CRS_EPSG
) -> dict:
    """
    Executes Stage 1 ingestion.
    Returns a dictionary of standardized GeoDataFrames.
    
    The zoning_layer_path is mandatory, per MASTER_PROJECT_PROMPT Section 5,
    because branching thresholds depend on zone classifications.
    """
    if not zoning_layer_path:
        raise ValueError("Zoning/Land-use layer is a MANDATORY input for Stage 1.")
        
    logger.info(f"Starting Stage 1 Ingestion. Target CRS: EPSG:{target_epsg}")
    
    # 1. Load Mandatory Zoning Layer
    logger.info(f"Loading zoning layer from {zoning_layer_path}...")
    gdf_zoning = load_vector_layer(zoning_layer_path, target_epsg=target_epsg)
    
    # Check if 'zone_type' column exists (used later for thresholds)
    if 'zone_type' not in gdf_zoning.columns:
        # Fallback or strict warning: if real data uses a different schema, map it here
        logger.warning("Zoning layer is missing 'zone_type' column. Ensure attributes are mapped correctly before Stage 2.")
    
    # 2. Load Optional Data Layers
    result = {
        "zoning": gdf_zoning,
        "target_epsg": target_epsg
    }
    
    if ai_extracted_layer_path:
        logger.info(f"Loading AI-extracted boundaries from {ai_extracted_layer_path}...")
        result["ai_extracted"] = load_vector_layer(ai_extracted_layer_path, target_epsg=target_epsg)
        
    if legacy_cadastral_layer_path:
        logger.info(f"Loading Legacy Cadastral vectors from {legacy_cadastral_layer_path}...")
        result["legacy_cadastral"] = load_vector_layer(legacy_cadastral_layer_path, target_epsg=target_epsg)
        
    logger.info("Stage 1 Ingestion completed successfully.")
    
    return result

if __name__ == "__main__":
    # Example usage / basic test
    logging.basicConfig(level=logging.INFO)
    try:
        run_stage1_ingestion(zoning_layer_path=None)
    except ValueError as e:
        print(f"Validation successful: {e}")
