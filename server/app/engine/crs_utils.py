"""
Dynamic CRS (Coordinate Reference System) Utilities
---------------------------------------------------
Handles projection of datasets to a unified, projected CRS (in meters)
required for accurate distance thresholds and IoU calculations.

The system requires an active working CRS depending on the Area of Interest (AOI).
"""

import geopandas as gpd

# Default to Meerut / NCR-UP pilot area (UTM Zone 43N)
# Target longitude is under 78E.
DEFAULT_WORKING_CRS_EPSG = 32643

def standardize_crs(gdf: gpd.GeoDataFrame, target_epsg: int = DEFAULT_WORKING_CRS_EPSG) -> gpd.GeoDataFrame:
    """
    Ensures a GeoDataFrame is projected to the target EPSG.
    Raises ValueError if the dataset has no defined CRS to begin with.
    """
    if gdf.crs is None:
        raise ValueError(
            "Input GeoDataFrame has no defined CRS. "
            "It must have a known CRS (e.g., WGS84) before it can be reprojected."
        )

    # If it's already in the target CRS, do nothing to avoid precision loss
    if gdf.crs.to_epsg() == target_epsg:
        return gdf

    return gdf.to_crs(epsg=target_epsg)

def get_crs_info(epsg_code: int) -> dict:
    """Returns basic details about the EPSG code using pyproj."""
    from pyproj import CRS
    crs_obj = CRS.from_epsg(epsg_code)
    return {
        "name": crs_obj.name,
        "is_projected": crs_obj.is_projected,
        "units": crs_obj.axis_info[0].unit_name if crs_obj.axis_info else "unknown"
    }
