"""
matcher — Core spatial matching engine for Stage 2 (Municipal Matching).

Business Rules (CODING_AGENT_MASTER_PROMPT.md §5):
- A municipal match does NOT require perfect geometric overlap or containment.
- If ANY meaningful spatial overlap exists between the AI-extracted structure
  and a municipal building record (including touching edges/boundaries),
  the structure passes Stage 2.
- Branch A (No municipal match):
  - status = "unregistered"
  - preserve AI geometry, structure_id, and provenance.
  - STOP processing this structure (does NOT proceed to cadastral validation).
- Branch B (Municipal overlap exists):
  - status = "municipal_matched" (eligible for Stage 3 Cadastral Validation).
  - preserve municipal record references and municipal attributes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import geopandas as gpd
from shapely.geometry import Polygon, mapping
from shapely.validation import make_valid

logger = logging.getLogger(__name__)


@dataclass
class MunicipalMatchedStructure:
    """Structure that has passed through Stage 2 municipal matching."""
    structure_id: str
    geometry: Polygon
    status: str                         # "unregistered" | "municipal_matched"
    reason: str
    municipal_building_id: str | None = None
    municipal_attributes: dict[str, Any] = field(default_factory=dict)
    original_properties: dict[str, Any] = field(default_factory=dict)

    def to_geojson_feature(self) -> dict:
        props = {
            **self.original_properties,
            "structure_id": self.structure_id,
            "status": self.status,
            "stage2_reason": self.reason,
            "municipal_building_id": self.municipal_building_id,
        }
        if self.municipal_attributes:
            props["municipal_record"] = self.municipal_attributes

        return {
            "type": "Feature",
            "geometry": mapping(self.geometry),
            "properties": props,
        }


def load_layer_in_crs(filepath: str | Path, target_epsg: int) -> gpd.GeoDataFrame:
    """Loads a GeoJSON vector file, repairs geometries, and projects to target EPSG."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"Vector dataset not found at: {filepath}")

    gdf = gpd.read_file(p)
    if gdf.empty:
        return gdf

    # Validate & repair invalid polygons
    gdf["geometry"] = gdf["geometry"].apply(
        lambda g: make_valid(g) if g is not None and not g.is_valid else g
    )
    gdf = gdf[gdf["geometry"].notnull() & ~gdf["geometry"].is_empty]

    if gdf.crs is None:
        raise ValueError(f"Dataset at {filepath} has no CRS defined.")

    if gdf.crs.to_epsg() != target_epsg:
        gdf = gdf.to_crs(epsg=target_epsg)

    return gdf


def match_structure(
    structure_geom: Polygon,
    municipal_gdf: gpd.GeoDataFrame,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Checks if a structure geometry intersects ANY municipal building in municipal_gdf.

    Returns:
        (has_match, municipal_building_id, municipal_attributes)
    """
    if municipal_gdf.empty:
        return False, None, {}

    # Query spatial index using bounding box
    candidates_idx = list(municipal_gdf.sindex.intersection(structure_geom.bounds))
    if not candidates_idx:
        return False, None, {}

    candidates = municipal_gdf.iloc[candidates_idx]

    # Find first candidate with actual spatial intersection (including boundaries/touches)
    for _, mun_row in candidates.iterrows():
        mun_geom = mun_row.geometry
        if structure_geom.intersects(mun_geom):
            mun_attrs = mun_row.to_dict()
            # Remove geometry from attributes dictionary
            mun_attrs.pop("geometry", None)

            # Determine building ID
            bld_id = str(mun_attrs.get("municipal_building_id") or mun_attrs.get("id") or "UNKNOWN_MUN_ID")
            return True, bld_id, mun_attrs

    return False, None, {}


def evaluate_municipal_matching(
    ai_extracted_gdf: gpd.GeoDataFrame,
    municipal_gdf: gpd.GeoDataFrame,
) -> tuple[list[MunicipalMatchedStructure], list[MunicipalMatchedStructure]]:
    """Evaluates all AI-extracted structures against municipal building records.

    Returns:
        (matched_structures, unregistered_structures)
    """
    matched: list[MunicipalMatchedStructure] = []
    unregistered: list[MunicipalMatchedStructure] = []

    for _, row in ai_extracted_gdf.iterrows():
        geom = row.geometry
        props = row.to_dict()
        props.pop("geometry", None)

        struct_id = str(props.get("structure_id") or props.get("id") or "UNKNOWN_STR_ID")

        has_match, mun_id, mun_attrs = match_structure(geom, municipal_gdf)

        if has_match:
            record = MunicipalMatchedStructure(
                structure_id=struct_id,
                geometry=geom,
                status="municipal_matched",
                reason=f"Spatially intersects municipal building record {mun_id}.",
                municipal_building_id=mun_id,
                municipal_attributes=mun_attrs,
                original_properties=props,
            )
            matched.append(record)
        else:
            record = MunicipalMatchedStructure(
                structure_id=struct_id,
                geometry=geom,
                status="unregistered",
                reason="No municipal building record overlaps this detected structure.",
                municipal_building_id=None,
                municipal_attributes={},
                original_properties=props,
            )
            unregistered.append(record)

    logger.info(
        "Stage 2 matching complete: %d matched (continue to Cadastral), %d unregistered (halted).",
        len(matched), len(unregistered),
    )
    return matched, unregistered
