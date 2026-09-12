"""
Ingestion Utilities
-------------------
Loads vector data from multiple sources (synthetic or real),
repairs legacy geometries, and enforces a standard CRS.
"""

import geopandas as gpd
from shapely.validation import make_valid
from app.engine.crs_utils import standardize_crs, DEFAULT_WORKING_CRS_EPSG
import os
import rasterio

def repair_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Repairs self-intersecting or invalid polygons often found in
    legacy digitized maps (e.g., Bhu-Naksha paper digitizations).
    """
    gdf = gdf.copy()
    
    # Use shapely.validation.make_valid
    gdf["geometry"] = gdf["geometry"].apply(
        lambda geom: make_valid(geom) if geom is not None and not geom.is_valid else geom
    )
    
    # Filter out null or empty geometries
    gdf = gdf[gdf["geometry"].notnull() & ~gdf["geometry"].is_empty]
    
    return gdf

def load_vector_layer(filepath: str, target_epsg: int = DEFAULT_WORKING_CRS_EPSG) -> gpd.GeoDataFrame:
    """
    Loads a vector file (GeoJSON, Shapefile, etc.), validates its geometry,
    and standardizes its CRS.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Vector file not found at: {filepath}")

    gdf = gpd.read_file(filepath)
    gdf = repair_geometries(gdf)
    gdf = standardize_crs(gdf, target_epsg)
    
    return gdf

def get_raster_metadata(filepath: str) -> dict:
    """
    Reads metadata from a raster file (like drone ORI) without loading
    the full pixel array into memory.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raster file not found at: {filepath}")
        
    with rasterio.open(filepath) as dataset:
        meta = dataset.meta.copy()
        bounds = dataset.bounds
        crs = dataset.crs
        
    return {
        "meta": meta,
        "bounds": bounds,
        "crs": crs
    }
