"""
validator — Core Cadastral Validation Engine for Stage 3.

Business Rules (CODING_AGENT_MASTER_PROMPT.md §6 & §7):
1. Input: Only structures that passed municipal matching (Stage 2).
2. Primary Parcel Rule:
   - The parcel containing the major part of the structure (largest intersection area)
     supplies `parcel_id`.
   - Other intersecting parcels are stored in `related_parcel_ids`.
   - Deterministic tie-break: smaller `parcel_id` alphabetically.
3. Overflow Measure:
   - Evaluates whether the structure is completely inside its primary parcel.
   - If not, computes the difference polygon and determines the maximum perpendicular
     exceedance distance from the primary parcel boundary in metres.
4. Threshold Classification:
   - Condition 1: overflow < threshold
     -> status = "verified" (eligible for Stage 4)
   - Condition 2: threshold <= overflow < 2 * threshold
     -> status = "audit_pending" (sent to human verification workflow)
   - Condition 3: overflow >= 2 * threshold
     -> status = "disputed" (sent to human verification workflow)
5. Preserves complete data model & provenance (§7):
   structure_id, geometry, status, parcel_id, related_parcel_ids,
   overflow_measure, configured_threshold, reason, municipality_reference,
   source/provenance, verification_method="geoai".
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import Point, Polygon, mapping
from shapely.validation import make_valid

logger = logging.getLogger(__name__)


@dataclass
class CadastralValidatedRecord:
    """Structure record enriched and validated against cadastral parcel boundaries."""
    structure_id: str
    geometry: Polygon
    status: str                         # "verified" | "audit_pending" | "disputed"
    parcel_id: str | None
    related_parcel_ids: list[str]
    overflow_measure: float             # Exceedance distance in metres
    configured_threshold: float
    reason: str
    municipality_reference: str | None
    source_tile: str | None
    source: str
    provenance: str
    verification_method: str = "geoai"
    cadastral_attributes: dict[str, Any] = field(default_factory=dict)
    original_properties: dict[str, Any] = field(default_factory=dict)

    def to_geojson_feature(self) -> dict:
        props = {
            **self.original_properties,
            "structure_id": self.structure_id,
            "status": self.status,
            "parcel_id": self.parcel_id,
            "related_parcel_ids": self.related_parcel_ids,
            "overflow_measure": round(self.overflow_measure, 4),
            "configured_threshold": self.configured_threshold,
            "reason": self.reason,
            "municipality_reference": self.municipality_reference,
            "source": self.source,
            "provenance": self.provenance,
            "verification_method": self.verification_method,
        }
        if self.cadastral_attributes:
            props["cadastral_record"] = self.cadastral_attributes

        return {
            "type": "Feature",
            "geometry": mapping(self.geometry),
            "properties": props,
        }


def compute_boundary_overflow_distance(structure_geom: Polygon, parcel_geom: Polygon) -> float:
    """Calculates the maximum exceedance distance (in metres) by which a structure

    extends beyond a parcel boundary. Returns 0.0 if completely within.
    """
    if structure_geom.within(parcel_geom):
        return 0.0

    diff = structure_geom.difference(parcel_geom)
    if diff.is_empty or diff.area <= 0:
        return 0.0

    # Collect coordinates of the difference polygon
    coords: list[tuple[float, float]] = []
    if diff.geom_type == "Polygon":
        coords.extend(diff.exterior.coords)
    elif diff.geom_type in ("MultiPolygon", "GeometryCollection"):
        for geom in diff.geoms:
            if hasattr(geom, "exterior"):
                coords.extend(geom.exterior.coords)

    if not coords:
        return 0.0

    # Max distance of overflow boundary points to the parcel polygon
    max_dist = max(Point(c).distance(parcel_geom) for c in coords)
    return float(max_dist)


def determine_primary_and_related_parcels(
    structure_geom: Polygon,
    parcels_gdf: gpd.GeoDataFrame,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Identifies the primary parcel (largest intersection area) and related parcels.

    Deterministic tie-break: smaller parcel_id alphabetically.
    Returns:
        (primary_parcel_dict, related_parcel_ids_list)
    """
    if parcels_gdf.empty:
        return None, []

    candidates_idx = list(parcels_gdf.sindex.intersection(structure_geom.bounds))
    if not candidates_idx:
        return None, []

    candidates = parcels_gdf.iloc[candidates_idx]

    intersecting_parcels: list[tuple[str, float, dict[str, Any]]] = []
    for _, row in candidates.iterrows():
        p_geom = row.geometry
        if structure_geom.intersects(p_geom):
            inter_area = structure_geom.intersection(p_geom).area
            if inter_area > 0:
                p_dict = row.to_dict()
                p_id = str(p_dict.get("parcel_id") or p_dict.get("id") or "UNKNOWN_PARCEL")
                intersecting_parcels.append((p_id, inter_area, p_dict))

    if not intersecting_parcels:
        return None, []

    # Sort primarily by intersection area descending, secondarily by parcel_id ascending (tie-break)
    intersecting_parcels.sort(key=lambda item: (-item[1], item[0]))

    primary_id, _, primary_dict = intersecting_parcels[0]
    related_ids = [item[0] for item in intersecting_parcels[1:]]

    return primary_dict, related_ids


def evaluate_structure_cadastral(
    structure_geom: Polygon,
    structure_props: dict[str, Any],
    parcels_gdf: gpd.GeoDataFrame,
    threshold: float = 10.0,
) -> CadastralValidatedRecord:
    """Validates a single structure against cadastral parcel boundaries."""
    sid = str(structure_props.get("structure_id") or "UNKNOWN_STR_ID")
    mun_ref = structure_props.get("municipal_building_id")
    source_tile = structure_props.get("source_tile")
    source = structure_props.get("source", "geoai")
    provenance = structure_props.get("provenance", "geoai_pipeline")

    primary_parcel, related_ids = determine_primary_and_related_parcels(structure_geom, parcels_gdf)

    if primary_parcel is None:
        return CadastralValidatedRecord(
            structure_id=sid,
            geometry=structure_geom,
            status="disputed",
            parcel_id=None,
            related_parcel_ids=[],
            overflow_measure=float("inf"),
            configured_threshold=threshold,
            reason="Structure does not intersect any cadastral land parcel.",
            municipality_reference=mun_ref,
            source_tile=source_tile,
            source=source,
            provenance=provenance,
            verification_method="geoai",
            cadastral_attributes={},
            original_properties=structure_props,
        )

    primary_id = str(primary_parcel.get("parcel_id") or "UNKNOWN_PARCEL")
    primary_geom = primary_parcel["geometry"]
    cad_attrs = {k: v for k, v in primary_parcel.items() if k != "geometry"}

    overflow = compute_boundary_overflow_distance(structure_geom, primary_geom)

    # Condition 1: Completely inside or overflow < threshold
    if overflow < threshold:
        status = "verified"
        if overflow == 0.0:
            reason = f"Structure is completely contained within cadastral parcel {primary_id}."
        else:
            reason = (
                f"Structure overflows parcel {primary_id} by {overflow:.2f} m, "
                f"which is within configured threshold ({threshold:.2f} m)."
            )
    # Condition 2: threshold <= overflow < 2 * threshold
    elif overflow < 2 * threshold:
        status = "audit_pending"
        related_str = f" and neighboring parcel(s) {', '.join(related_ids)}" if related_ids else ""
        reason = (
            f"Overflow on parcel {primary_id}{related_str} exceeds threshold ({threshold:.2f} m) "
            f"at {overflow:.2f} m, but remains below 2x threshold ({2 * threshold:.2f} m)."
        )
    # Condition 3: overflow >= 2 * threshold
    else:
        status = "disputed"
        related_str = f" and neighboring parcel(s) {', '.join(related_ids)}" if related_ids else ""
        reason = (
            f"Major overflow on parcel {primary_id}{related_str} exceeds 2x threshold "
            f"({2 * threshold:.2f} m) with measured exceedance of {overflow:.2f} m."
        )

    return CadastralValidatedRecord(
        structure_id=sid,
        geometry=structure_geom,
        status=status,
        parcel_id=primary_id,
        related_parcel_ids=related_ids,
        overflow_measure=overflow,
        configured_threshold=threshold,
        reason=reason,
        municipality_reference=mun_ref,
        source_tile=source_tile,
        source=source,
        provenance=provenance,
        verification_method="geoai",
        cadastral_attributes=cad_attrs,
        original_properties=structure_props,
    )


def validate_cadastral_dataset(
    matched_gdf: gpd.GeoDataFrame,
    parcels_gdf: gpd.GeoDataFrame,
    threshold: float = 10.0,
) -> tuple[list[CadastralValidatedRecord], list[CadastralValidatedRecord], list[CadastralValidatedRecord]]:
    """Evaluates all municipally-matched structures against cadastral parcels.

    Returns:
        (verified_records, audit_pending_records, disputed_records)
    """
    verified: list[CadastralValidatedRecord] = []
    audit_pending: list[CadastralValidatedRecord] = []
    disputed: list[CadastralValidatedRecord] = []

    for _, row in matched_gdf.iterrows():
        sgeom = row.geometry
        props = row.to_dict()
        props.pop("geometry", None)

        record = evaluate_structure_cadastral(sgeom, props, parcels_gdf, threshold=threshold)

        if record.status == "verified":
            verified.append(record)
        elif record.status == "audit_pending":
            audit_pending.append(record)
        elif record.status == "disputed":
            disputed.append(record)

    logger.info(
        "Stage 3 Cadastral Validation complete: %d verified (eligible for Stage 4), "
        "%d audit_pending (human verification), %d disputed (human verification).",
        len(verified), len(audit_pending), len(disputed),
    )
    return verified, audit_pending, disputed
