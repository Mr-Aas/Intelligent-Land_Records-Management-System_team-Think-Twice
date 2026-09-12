"""
Stage 4 Multi-Department Data Integration & Consolidation Runner (§9, §10, §24).

Orchestrates:
1. Loading eligible `verified` spatial structures (from GeoAI Stage 3 and Human Verification).
2. Ingesting 5 government departmental datasets:
   - Revenue Department
   - Urban Local Body (ULB)
   - Urban Development Authority (UDA)
   - Registration and Stamps Department
   - Directorate of Land Records (DLR)
3. Grouping by land parcel ID.
4. Executing the swappable conflict resolution engine (SmartRuleConflictResolver).
5. Generating the consolidated Single Source of Truth parcel records:
   - `data/outputs/stage4_consolidated_parcels.json`
   - `data/outputs/stage4_consolidated_parcels.geojson`
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.pipeline import config
from app.pipeline.stage4.resolver import ConflictResolver, SmartRuleConflictResolver


def _load_csv_by_parcel_id(path_str: str) -> Dict[str, Dict[str, Any]]:
    """Load a departmental CSV and index rows by parcel_id."""
    path = Path(path_str)
    records: Dict[str, Dict[str, Any]] = {}
    if not path.exists():
        return records

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get("parcel_id")
            if pid:
                records[pid] = dict(row)
    return records


def _load_geojson(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(data: Any, path_str: str) -> None:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_eligible_verified_structures() -> List[Dict[str, Any]]:
    """
    Collect all spatial structures eligible for Stage 4 (§9, §17).

    Eligible structures:
    - Stage 3 GeoAI verified structures (`stage3_verified.geojson`)
    - Human-verified structures (`human_verification_records.geojson` with status == 'verified')

    Strictly excluded (§9, §11, §17):
    - `unregistered`
    - `audit_pending`
    - `disputed`
    - `locked_disputed`
    """
    eligible_by_id: Dict[str, Dict[str, Any]] = {}

    # 1. GeoAI Stage 3 verified
    stage3_fc = _load_geojson(config.STAGE3_VERIFIED_OUTPUT_PATH)
    for feat in stage3_fc.get("features", []):
        sid = feat.get("properties", {}).get("structure_id")
        status = feat.get("properties", {}).get("status")
        if sid and status == "verified":
            eligible_by_id[sid] = feat

    # 2. Human verification records (overlay decisions)
    human_fc = _load_geojson(config.HUMAN_VERIFICATION_RECORDS_PATH)
    for feat in human_fc.get("features", []):
        sid = feat.get("properties", {}).get("structure_id")
        status = feat.get("properties", {}).get("status")
        if sid:
            if status == "verified":
                # Eligible: either human-verified or transitioned to verified
                eligible_by_id[sid] = feat
            elif status == "locked_disputed":
                # Explicitly remove if previously in eligible pool
                eligible_by_id.pop(sid, None)

    return list(eligible_by_id.values())


def run_stage4(
    resolver: Optional[ConflictResolver] = None,
) -> Dict[str, Any]:
    """
    Execute Stage 4 multi-department consolidation and conflict resolution.

    Returns execution summary with consolidated parcel counts and output paths.
    """
    if resolver is None:
        resolver = SmartRuleConflictResolver()

    # 1. Ingest eligible verified structures and group by parcel_id
    verified_structures = get_eligible_verified_structures()
    structures_by_parcel: Dict[str, List[Dict[str, Any]]] = {}
    for feat in verified_structures:
        props = feat.get("properties", {})
        pid = props.get("parcel_id") or props.get("primary_parcel_id")
        if pid:
            structures_by_parcel.setdefault(pid, []).append(feat)

    # 2. Ingest Cadastral Parcels
    cadastral_fc = _load_geojson(config.CADASTRAL_DATA_PATH)
    cadastral_by_id: Dict[str, Dict[str, Any]] = {}
    for feat in cadastral_fc.get("features", []):
        pid = feat.get("properties", {}).get("parcel_id")
        if pid:
            cadastral_by_id[pid] = feat

    # 3. Ingest 5 Departmental Datasets (§9)
    dept_revenue = _load_csv_by_parcel_id(config.REVENUE_DATA_PATH)
    dept_ulb = _load_csv_by_parcel_id(config.ULB_DATA_PATH)
    dept_uda = _load_csv_by_parcel_id(config.UDA_DATA_PATH)
    dept_registration = _load_csv_by_parcel_id(config.REGISTRATION_DATA_PATH)
    dept_dlr = _load_csv_by_parcel_id(config.DLR_DATA_PATH)

    # 4. Enumerate all unique parcel IDs
    all_parcel_ids = sorted(
        set(cadastral_by_id.keys())
        | set(dept_revenue.keys())
        | set(dept_ulb.keys())
        | set(dept_uda.keys())
        | set(dept_registration.keys())
        | set(dept_dlr.keys())
        | set(structures_by_parcel.keys())
    )

    # 5. Resolve conflicts parcel by parcel
    consolidated_parcels: List[Dict[str, Any]] = []
    geojson_features: List[Dict[str, Any]] = []
    conflicted_parcels_count = 0

    for pid in all_parcel_ids:
        cad_feat = cadastral_by_id.get(pid)
        dept_records = {
            "revenue_department": dept_revenue.get(pid, {}),
            "urban_local_body": dept_ulb.get(pid, {}),
            "urban_development_authority": dept_uda.get(pid, {}),
            "registration_stamps": dept_registration.get(pid, {}),
            "directorate_land_records": dept_dlr.get(pid, {}),
        }
        # Filter out empty department entries
        active_dept_records = {
            k: v for k, v in dept_records.items() if v
        }

        parcel_structures = structures_by_parcel.get(pid, [])

        resolved_record = resolver.resolve_parcel(
            parcel_id=pid,
            cadastral_feature=cad_feat,
            department_records=active_dept_records,
            verified_structures=parcel_structures,
        )

        consolidated_parcels.append(resolved_record)

        if resolved_record.get("conflict_summary", {}).get("has_conflicts"):
            conflicted_parcels_count += 1

        # Build GeoJSON feature
        geometry = cad_feat.get("geometry") if cad_feat else None
        geojson_features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": resolved_record,
        })

    # 6. Save Single Source of Truth artifacts (§10)
    _save_json(consolidated_parcels, config.STAGE4_CONSOLIDATED_JSON_PATH)

    geojson_collection = {
        "type": "FeatureCollection",
        "name": "stage4_consolidated_parcels",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": geojson_features,
    }
    _save_json(geojson_collection, config.STAGE4_CONSOLIDATED_GEOJSON_PATH)

    return {
        "status": "success",
        "total_parcels_consolidated": len(consolidated_parcels),
        "total_eligible_verified_structures": len(verified_structures),
        "conflicted_parcels_count": conflicted_parcels_count,
        "json_output_path": config.STAGE4_CONSOLIDATED_JSON_PATH,
        "geojson_output_path": config.STAGE4_CONSOLIDATED_GEOJSON_PATH,
    }


if __name__ == "__main__":
    result = run_stage4()
    print(json.dumps(result, indent=2))
