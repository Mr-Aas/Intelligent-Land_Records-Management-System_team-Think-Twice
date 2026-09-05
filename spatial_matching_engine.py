"""
Stage 2: Spatial Matching Engine
---------------------------------
Purpose:
    Resolve overlapping/gapped parcel boundaries ("sliver polygons") that
    result from merging two vector sources of differing origin/accuracy
    (e.g., old Revenue Dept. cadastral vectors vs. new AI-extracted /
    Municipal GIS parcel vectors), and bind matching parcels together
    using Intersection over Union (IoU).

Pipeline position:
    [AI Feature Extraction: SAM/YOLO output] ---\
                                                   >--> THIS MODULE --> [Stage 2: Entity Resolution]
    [Existing Cadastral / Municipal vectors] ---/

Inputs:
    - source_a: GeoDataFrame  (e.g., old Revenue Dept. cadastral parcels)
    - source_b: GeoDataFrame  (e.g., new AI-extracted / drone-derived parcels)
      Both MUST be reprojected to the same CRS before calling this module.

Outputs:
    - matched_pairs: DataFrame of (source_a id, source_b id, IoU score, match_status)
    - cleaned_gdf: GeoDataFrame with sliver polygons healed/removed
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

# ---------------------------------------------------------------------------
# CONFIG — tune these against real department data before deployment
# ---------------------------------------------------------------------------
IOU_MATCH_THRESHOLD = 0.85       # >= this IoU => same real-world parcel (per your doc's Stage 2 rule)
IOU_REVIEW_THRESHOLD = 0.40      # between REVIEW and MATCH => flag for human/legal review
SLIVER_AREA_RATIO_THRESHOLD = 0.02   # sliver if area < 2% of the smaller parent parcel
SLIVER_ABSOLUTE_AREA_M2 = 5.0        # OR sliver if absolute area < 5 sq. meters (tune per parcel density)
WORKING_CRS_EPSG = 32644          # Example: UTM Zone 44N — replace with the correct zone for your project's AOI


# ---------------------------------------------------------------------------
# 1. CRS / VALIDITY GUARDRAILS
# ---------------------------------------------------------------------------
def ensure_common_crs(gdf_a: gpd.GeoDataFrame, gdf_b: gpd.GeoDataFrame, target_epsg: int = WORKING_CRS_EPSG):
    """
    Both datasets must share one projected CRS (in meters) before any
    area/IoU math is valid. Geographic CRS (e.g., WGS84 lat/lon) will
    give meaningless area/overlap values.
    """
    if gdf_a.crs is None or gdf_b.crs is None:
        raise ValueError("Both GeoDataFrames must have a defined CRS before matching.")

    gdf_a = gdf_a.to_crs(epsg=target_epsg)
    gdf_b = gdf_b.to_crs(epsg=target_epsg)
    return gdf_a, gdf_b


def fix_invalid_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Old scanned/digitized cadastral data very commonly has self-intersecting
    or invalid polygons. This repairs them before any spatial operation,
    otherwise Shapely will throw errors or silently return wrong results.
    """
    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].apply(
        lambda geom: make_valid(geom) if geom is not None and not geom.is_valid else geom
    )
    gdf = gdf[gdf["geometry"].notnull() & ~gdf["geometry"].is_empty]
    return gdf


# ---------------------------------------------------------------------------
# 2. IoU-BASED SPATIAL MATCHING (Stage 2 core logic from your research doc)
# ---------------------------------------------------------------------------
def compute_iou(geom_a, geom_b) -> float:
    """Standard IoU: intersection area / union area."""
    if geom_a is None or geom_b is None or geom_a.is_empty or geom_b.is_empty:
        return 0.0
    intersection = geom_a.intersection(geom_b)
    if intersection.is_empty:
        return 0.0
    union = geom_a.union(geom_b)
    if union.area == 0:
        return 0.0
    return intersection.area / union.area


def match_parcels(source_a: gpd.GeoDataFrame,
                   source_b: gpd.GeoDataFrame,
                   id_col_a: str,
                   id_col_b: str) -> pd.DataFrame:
    """
    For every parcel in source_a, find candidate overlapping parcels in
    source_b (via spatial index for performance), compute IoU, and
    classify the match.

    Returns a flat DataFrame — one row per candidate pair — with columns:
        id_a, id_b, iou_score, match_status
    match_status in {"MATCHED", "REVIEW_NEEDED", "NO_MATCH"}
    """
    # Build spatial index on source_b once — avoids an O(n*m) brute-force scan
    sindex = source_b.sindex

    records = []
    for _, row_a in source_a.iterrows():
        geom_a = row_a.geometry
        if geom_a is None or geom_a.is_empty:
            continue

        # Narrow candidates first using bounding-box intersection (fast),
        # then confirm with true geometric overlap
        candidate_idxs = list(sindex.intersection(geom_a.bounds))
        candidates = source_b.iloc[candidate_idxs]

        found_match = False
        for _, row_b in candidates.iterrows():
            geom_b = row_b.geometry
            if geom_b is None or geom_b.is_empty or not geom_a.intersects(geom_b):
                continue

            iou = compute_iou(geom_a, geom_b)
            if iou <= 0:
                continue

            if iou >= IOU_MATCH_THRESHOLD:
                status = "MATCHED"
                found_match = True
            elif iou >= IOU_REVIEW_THRESHOLD:
                status = "REVIEW_NEEDED"
            else:
                status = "NO_MATCH"

            records.append({
                "id_a": row_a[id_col_a],
                "id_b": row_b[id_col_b],
                "iou_score": round(iou, 4),
                "match_status": status,
            })

        if not found_match and len(candidates) == 0:
            records.append({
                "id_a": row_a[id_col_a],
                "id_b": None,
                "iou_score": 0.0,
                "match_status": "NO_MATCH",
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 3. SLIVER POLYGON DETECTION & HEALING (Geometric Inconsistencies)
# ---------------------------------------------------------------------------
def detect_sliver_polygons(gdf: gpd.GeoDataFrame,
                            parent_area_lookup: dict = None) -> gpd.GeoDataFrame:
    """
    Flags tiny gap/overlap artifacts produced when two vector sources of
    different accuracy are overlaid (classic old-hand-drawn-map vs.
    modern-drone-map problem from your doc's Section 3).

    A polygon is flagged as a sliver if EITHER:
        (a) its area is below an absolute threshold, OR
        (b) its area is below a ratio of a reference "parent" parcel area
    """
    gdf = gdf.copy()
    gdf["area_m2"] = gdf.geometry.area

    def is_sliver(row):
        if row["area_m2"] < SLIVER_ABSOLUTE_AREA_M2:
            return True
        if parent_area_lookup:
            parent_area = parent_area_lookup.get(row.name)
            if parent_area and (row["area_m2"] / parent_area) < SLIVER_AREA_RATIO_THRESHOLD:
                return True
        return False

    gdf["is_sliver"] = gdf.apply(is_sliver, axis=1)
    return gdf


def heal_slivers(gdf: gpd.GeoDataFrame, snap_tolerance: float = 0.15) -> gpd.GeoDataFrame:
    """
    Removes sliver polygons and snaps remaining boundaries together within
    a small tolerance (in meters, since we're in a projected CRS).

    This is a simplified topology-correction pass:
      1. Drop polygons flagged as slivers
      2. Buffer(0) trick to fix minor self-intersections after edits
      3. (Optional/advanced) snapping neighboring edges within tolerance
         should be done with a dedicated topology library (e.g., a
         GRASS GIS `v.clean` call, or `topojson`) for production-grade
         snapping — flagged here as a follow-up integration point.
    """
    cleaned = gdf[~gdf["is_sliver"]].copy()
    cleaned["geometry"] = cleaned["geometry"].buffer(0)  # heals minor self-intersections
    cleaned = cleaned[cleaned.geometry.notnull() & ~cleaned.geometry.is_empty]
    return cleaned.drop(columns=["is_sliver"], errors="ignore")


# ---------------------------------------------------------------------------
# 4. ORCHESTRATION — how Stage 1 output flows into this module
# ---------------------------------------------------------------------------
def run_stage2_matching(source_a_path: str,
                         source_b_path: str,
                         id_col_a: str = "khasra_no",
                         id_col_b: str = "parcel_id"):
    """
    End-to-end entry point for this module.

    source_a_path: path to old Revenue Dept. cadastral vector file (e.g., .shp / .geojson)
    source_b_path: path to AI-extracted / municipal parcel vector file
    """
    gdf_a = gpd.read_file(source_a_path)
    gdf_b = gpd.read_file(source_b_path)

    gdf_a, gdf_b = ensure_common_crs(gdf_a, gdf_b)
    gdf_a = fix_invalid_geometries(gdf_a)
    gdf_b = fix_invalid_geometries(gdf_b)

    match_results = match_parcels(gdf_a, gdf_b, id_col_a, id_col_b)

    # Sliver detection is run on the union footprint of overlapping pairs —
    # in production, restrict this to the actual overlap/gap geometries
    # rather than raw parcels; simplified here for framework clarity.
    gdf_b_flagged = detect_sliver_polygons(gdf_b)
    gdf_b_cleaned = heal_slivers(gdf_b_flagged)

    return match_results, gdf_b_cleaned


# ---------------------------------------------------------------------------
# Example usage (replace paths with real department exports)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    matches_df, cleaned_parcels = run_stage2_matching(
        source_a_path="revenue_cadastral_old.geojson",
        source_b_path="ai_extracted_parcels_new.geojson",
        id_col_a="khasra_no",
        id_col_b="parcel_id",
    )

    print("Match summary:")
    print(matches_df["match_status"].value_counts())
    print("\nSample matches:")
    print(matches_df.head(10))

    cleaned_parcels.to_file("cleaned_parcels_stage2_output.geojson", driver="GeoJSON")
    matches_df.to_csv("stage2_match_results.csv", index=False)
