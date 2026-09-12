"""
Stage 2: Semantic/Text Engine (Attribute Phase) & Spatial Matching
-------------------------------------------------------------------
Implements Star Topology Snapping against Priority 1 (GNSS) Anchor data.
Uses a Three-Tier Traffic Light model based on zone-specific thresholds.
Defers conflicts to PENDING_SURVEY if Priority 1 data is missing.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
import logging
import os
import uuid
from app.engine.ingestion import load_vector_layer

logger = logging.getLogger(__name__)

# Zone Distance Thresholds (in meters)
THRESHOLDS_M = {
    "Dense Urban": 0.10,
    "Suburban": 0.15,
    "Agricultural": 0.30
}

def get_zone_threshold(geom, zoning_gdf: gpd.GeoDataFrame) -> float:
    """Finds the zone type for a given geometry and returns its threshold."""
    # Find intersecting zone
    # For simplicity, grab the first intersecting zone
    intersects = zoning_gdf[zoning_gdf.intersects(geom)]
    if intersects.empty:
        # Fallback to strictest if no zone found
        return THRESHOLDS_M["Dense Urban"]
        
    zone_type = intersects.iloc[0].get("zone_type", "Dense Urban")
    return THRESHOLDS_M.get(zone_type, 0.10)

def calculate_boundary_distance(geom_a, geom_b) -> float:
    """
    Calculates Hausdorff distance explicitly on boundaries with densify_frac
    to avoid underestimating discrepancies on sparsely-vertexed edges.
    """
    if geom_a is None or geom_b is None or geom_a.is_empty or geom_b.is_empty:
        return float('inf')
    
    import shapely
    # GEOS discrete Hausdorff distance on boundary
    return shapely.hausdorff_distance(geom_a.boundary, geom_b.boundary, densify=0.05)

def check_overlap(geom, other_gdf: gpd.GeoDataFrame) -> bool:
    """Returns True if geom overlaps with any geometry in other_gdf."""
    if other_gdf is None or other_gdf.empty:
        return False
    return not other_gdf[other_gdf.intersects(geom)].empty

def run_stage2_matching(stage1_results: dict, anchor_layer_path: str = None) -> dict:
    """
    Executes Stage 2 spatial matching.
    stage1_results contains standardized zoning, ai_extracted (Priority 2), legacy (Priority 3).
    """
    zoning_gdf = stage1_results.get("zoning")
    ai_gdf = stage1_results.get("ai_extracted")
    legacy_gdf = stage1_results.get("legacy_cadastral")
    target_epsg = stage1_results.get("target_epsg")
    
    anchor_gdf = None
    if anchor_layer_path and os.path.exists(anchor_layer_path):
        anchor_gdf = load_vector_layer(anchor_layer_path, target_epsg=target_epsg)
        
    results = []
    
    # Combine Priority 2 (AI) and Priority 3 (Legacy) to process them uniformly
    # against Priority 1 (Anchor). 
    # In a real scenario, we might track their origin source.
    process_queue = []
    if ai_gdf is not None and not ai_gdf.empty:
        for idx, row in ai_gdf.iterrows():
            process_queue.append({"geom": row.geometry, "source": "Priority 2", "attributes": row.to_dict()})
            
    if legacy_gdf is not None and not legacy_gdf.empty:
        for idx, row in legacy_gdf.iterrows():
            process_queue.append({"geom": row.geometry, "source": "Priority 3", "attributes": row.to_dict()})
            
    # If no Priority 1 data available for the region:
    if anchor_gdf is None or anchor_gdf.empty:
        logger.warning("Priority 1 (GNSS/Anchor) is missing. Activating pre-check-and-defer rule.")
        return "priority 1 is not present"
        for item in process_queue:

            geom = item["geom"]
            source = item["source"]
            
            # Check for new-parcel bypass: zero overlaps across all sources
            # Priority 2 checks against Priority 3; Priority 3 checks against Priority 2.
            has_overlap = False
            if source == "Priority 2" and check_overlap(geom, legacy_gdf):
                has_overlap = True
                print(f"legacy data checkOverlap result {check_overlap(geom,legacy_gdf)} ")
            elif source == "Priority 3" and check_overlap(geom, ai_gdf):
                has_overlap = True
                print(f"ai data checkOverlap result {check_overlap(geom,ai_gdf)} ")
                
            if not has_overlap:
                # Bypass -> Straight to VERIFIED
                results.append({
                    "geometry": geom,
                    "status": "VERIFIED",
                    "reason": "New parcel bypass (no overlaps, no conflicts)",
                    "attributes": item["attributes"]
                })
            else:
                # Disagreement but no Priority 1 -> PENDING_SURVEY
                results.append({
                    "geometry": geom,
                    "status": "PENDING_SURVEY",
                    "reason": f"Missing GNSS/CORS anchor to resolve {source} overlap",
                    "attributes": item["attributes"]
                })
                
    else:
        # Priority 1 is present. Proceed with Star Topology.
        print(f" data of anchor_gdf priority1 \n {anchor_gdf}")
        anchor_sindex = anchor_gdf.sindex
        
        for item in process_queue:
            geom = item["geom"]
            source = item["source"]
            
            # Find closest/intersecting anchor
            possible_matches_index = list(anchor_sindex.intersection(geom.bounds))
            possible_matches = anchor_gdf.iloc[possible_matches_index]
            
            if possible_matches.empty:
                # No anchor nearby. Treat like missing anchor for this parcel.
                results.append({
                    "geometry": geom,
                    "status": "PENDING_SURVEY",
                    "reason": "No GNSS/CORS anchor found for this specific parcel area",
                    "attributes": item["attributes"]
                })
                continue
                
            # Find the best overlapping anchor (max intersection area)
            best_anchor = None
            max_area = -1
            for _, anchor_row in possible_matches.iterrows():
                intersection_area = geom.intersection(anchor_row.geometry).area
                if intersection_area > max_area:
                    max_area = intersection_area
                    best_anchor = anchor_row
                    
            if max_area <= 0:
                results.append({
                    "geometry": geom,
                    "status": "PENDING_SURVEY",
                    "reason": "No GNSS/CORS anchor overlap found for this specific parcel area",
                    "attributes": item["attributes"]
                })
                continue
                
            # Calculate Boundary Hausdorff Distance (densify_frac=0.05)
            anchor_geom = best_anchor.geometry
            dist = calculate_boundary_distance(geom, anchor_geom)
            threshold = get_zone_threshold(geom, zoning_gdf)
            
            # Traffic Light Branching
            if dist <= threshold:
                status = "VERIFIED"
                # Auto-heal: snap to anchor geometry (take anchor geometry as truth)
                final_geom = anchor_geom 
                reason = f"Green branch: {dist:.3f}m <= {threshold}m"
            elif dist <= 2 * threshold:
                status = "AUDIT_PENDING"
                # Tentative merge: keep original geometry, flag for audit
                final_geom = geom
                reason = f"Amber branch: {dist:.3f}m > {threshold}m but <= {2*threshold}m"
            else:
                status = "LOCKED_DISPUTE"
                # Hard lock: freeze parcel, route to dashboard
                final_geom = geom
                reason = f"Red branch: {dist:.3f}m > {2*threshold}m"
                
            # Merge attributes from Anchor
            merged_attrs = item["attributes"].copy()
            merged_attrs.update(best_anchor.to_dict())
            
            results.append({
                "geometry": final_geom,
                "status": status,
                "reason": reason,
                "distance_m": dist,
                "threshold_m": threshold,
                "attributes": merged_attrs
            })
            
    out_gdf = gpd.GeoDataFrame(results, crs=f"EPSG:{target_epsg}")
    return out_gdf

if __name__ == "__main__":
    pass
