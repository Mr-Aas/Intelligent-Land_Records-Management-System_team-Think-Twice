"""
Synthetic Data Generator
------------------------
Generates mock overlapping parcels and zoning layers for Phase 1 & 2 unit testing.
Created in WGS84 (EPSG:4326) to test the reprojection logic to UTM (e.g. EPSG:32643).
"""

import geopandas as gpd
from shapely.geometry import Polygon
import os

def create_mock_data(output_dir: str = "data/synthetic"):
    os.makedirs(output_dir, exist_ok=True)
    
    # Base coordinate (Somewhere in Meerut, UP: roughly 28.98°N, 77.70°E)
    lon, lat = 77.7000, 28.9800
    
    # 1. Create a Zoning Layer (Mandatory for Stage 1)
    # Covering a slightly larger area
    zone_poly_1 = Polygon([
        (lon-0.01, lat-0.01), (lon+0.01, lat-0.01), 
        (lon+0.01, lat+0.01), (lon-0.01, lat+0.01)
    ])
    gdf_zoning = gpd.GeoDataFrame({
        "zone_id": ["Z-001"],
        "zone_type": ["Dense Urban"]
    }, geometry=[zone_poly_1], crs="EPSG:4326")
    
    # 2. Create AI-Extracted Boundaries (High Priority)
    ai_poly_1 = Polygon([
        (lon, lat), (lon+0.001, lat), 
        (lon+0.001, lat+0.001), (lon, lat+0.001)
    ])
    gdf_ai = gpd.GeoDataFrame({
        "parcel_id": ["AI-101"],
        "confidence": [0.95]
    }, geometry=[ai_poly_1], crs="EPSG:4326")
    
    # 3. Create Legacy Cadastral Boundaries (Lower Priority)
    # Intentionally shifted slightly to simulate a "sliver" or threshold conflict
    leg_poly_1 = Polygon([
        (lon+0.0001, lat+0.0001), (lon+0.0011, lat+0.0001), 
        (lon+0.0011, lat+0.0011), (lon+0.0001, lat+0.0011)
    ])
    # And a self-intersecting invalid polygon to test repair logic
    leg_poly_2 = Polygon([
        (lon-0.001, lat-0.001), (lon-0.002, lat-0.001),
        (lon-0.001, lat-0.002), (lon-0.002, lat-0.002) # Bow-tie intersection
    ])
    
    gdf_legacy = gpd.GeoDataFrame({
        "khasra_no": ["LEG-101", "LEG-102"],
        "owner": ["Ram Kumar", "Shyam Singh"]
    }, geometry=[leg_poly_1, leg_poly_2], crs="EPSG:4326")
    
    # 4. Create Priority 1 Anchor Data (GNSS/NAKSHA)
    # The absolute truth. Notice it is slightly different from legacy, and matches AI.
    anchor_poly_1 = Polygon([
        (lon, lat), (lon+0.001, lat), 
        (lon+0.001, lat+0.001), (lon, lat+0.001)
    ])
    gdf_anchor = gpd.GeoDataFrame({
        "bhu_aadhar_ulpin": ["UP-12345678901234"]
    }, geometry=[anchor_poly_1], crs="EPSG:4326")
    
    # Export to GeoJSON
    # zoning_path = os.path.join(output_dir, "mock_zoning.geojson")
    # ai_path = os.path.join(output_dir, "mock_ai_extracted.geojson")
    # legacy_path = os.path.join(output_dir, "mock_legacy_cadastral.geojson")
    # anchor_path = os.path.join(output_dir, "mock_anchor.geojson")
    zoning_path = "e:/projects/sih-2026-project-1/data/real/zoningdata.geojson"
    ai_path = "e:/projects/sih-2026-project-1/data/real/ai_extracteddata.geojson"
    legacy_path = "e:/projects/sih-2026-project-1/data/real/cadastrialdata.geojson"
    anchor_path = "e:/projects/sih-2026-project-1/data/real/gnssdata.geojson"

    gdf_zoning.to_file(zoning_path, driver="GeoJSON")
    gdf_ai.to_file(ai_path, driver="GeoJSON")
    gdf_legacy.to_file(legacy_path, driver="GeoJSON")
    gdf_anchor.to_file(anchor_path, driver="GeoJSON")
    
    print(f"Generated synthetic test data in {output_dir}")

if __name__ == "__main__":
    import os
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'synthetic_v2'))
    create_mock_data(base_dir)
