"""
FastAPI REST Endpoints for Human Verification & Stage 4 Integration (§8, §9, §10, §13).

Provides:
- Synthetic authentication for Lekhpal/Patwari officials.
- Tehsil-scoped human verification review queues.
- Human decision actions (`mark_verified`, `lock_disputed`).
- Stage 4 consolidation trigger and Single Source of Truth parcel queries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.pipeline import config
from app.pipeline.human_verification import service as hv_service
from app.pipeline.stage4 import runner as stage4_runner

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., description="Synthetic username (e.g. 'official_alpha')")
    password: str = Field(..., description="Password (e.g. 'password123')")


class HumanActionRequest(BaseModel):
    structure_id: str = Field(..., description="Target structure ID (e.g. 'STR-005')")
    official_id: str = Field(..., description="Official performing the action")
    action: Literal["mark_verified", "lock_disputed"] = Field(
        ..., description="Exact decision action (§8)"
    )
    notes: str = Field(default="", description="Optional official notes or remarks")


# ---------------------------------------------------------------------------
# Authentication Endpoints (§8)
# ---------------------------------------------------------------------------
@router.post("/auth/login")
def login(payload: LoginRequest):
    """Authenticate synthetic official credentials."""
    official = hv_service.authenticate(payload.username, payload.password)
    if not official:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    return {
        "status": "success",
        "message": f"Welcome, {official['name']} ({official['role']})",
        "user": official,
    }


# ---------------------------------------------------------------------------
# Human Verification Endpoints (§8)
# ---------------------------------------------------------------------------
@router.get("/human-verification/queue")
def get_verification_queue(
    official_id: str = Query(..., description="Official ID to scope by tehsil"),
    include_decided: bool = Query(False, description="Include already decided items"),
):
    """Retrieve tehsil-filtered audit_pending and disputed structures."""
    try:
        queue = hv_service.get_verification_queue(
            official_id=official_id,
            include_decided=include_decided,
        )
        official = hv_service.get_official(official_id)
        return {
            "status": "success",
            "official_id": official_id,
            "tehsil": official["tehsil"] if official else None,
            "count": len(queue),
            "features": queue,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/human-verification/action")
def perform_human_action(payload: HumanActionRequest):
    """
    Perform a human decision action (§8):
    - `mark_verified`: Transition to `verified`, eligible for Stage 4.
    - `lock_disputed`: Transition to `locked_disputed`, frozen and excluded from Stage 4.
    """
    try:
        if payload.action == "mark_verified":
            feature = hv_service.mark_verified(
                structure_id=payload.structure_id,
                official_id=payload.official_id,
                notes=payload.notes,
            )
        elif payload.action == "lock_disputed":
            feature = hv_service.lock_disputed(
                structure_id=payload.structure_id,
                official_id=payload.official_id,
                notes=payload.notes,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported action: {payload.action}",
            )
        return {
            "status": "success",
            "action": payload.action,
            "structure_id": payload.structure_id,
            "feature": feature,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/human-verification/audit-log")
def get_audit_log():
    """Retrieve full append-only audit trail of human actions."""
    path = Path(config.HUMAN_AUDIT_LOG_PATH)
    if not path.exists():
        return {"status": "success", "count": 0, "entries": []}
    with open(path, "r", encoding="utf-8") as f:
        try:
            entries = json.load(f)
        except json.JSONDecodeError:
            entries = []
    return {"status": "success", "count": len(entries), "entries": entries}


# ---------------------------------------------------------------------------
# Stage 4 Consolidation Endpoints (§9, §10, §24)
# ---------------------------------------------------------------------------
@router.post("/stage4/run")
def trigger_stage4_consolidation():
    """Trigger the Stage 4 multi-department consolidation and conflict resolution pipeline."""
    try:
        result = stage4_runner.run_stage4()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage 4 pipeline error: {str(e)}",
        )


@router.get("/stage4/parcels")
def get_consolidated_parcels(
    tehsil: Optional[str] = Query(None, description="Filter by tehsil"),
    format: Literal["json", "geojson"] = Query("json", description="Output format"),
):
    """Retrieve consolidated Single Source of Truth parcel records."""
    if format == "geojson":
        geojson_path = Path(config.STAGE4_CONSOLIDATED_GEOJSON_PATH)
        if not geojson_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stage 4 GeoJSON output not generated yet. Trigger /api/stage4/run first.",
            )
        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if tehsil:
            filtered_features = [
                feat for feat in data.get("features", [])
                if feat.get("properties", {}).get("tehsil") == tehsil
            ]
            data["features"] = filtered_features
        return data

    json_path = Path(config.STAGE4_CONSOLIDATED_JSON_PATH)
    if not json_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage 4 consolidated output not generated yet. Trigger /api/stage4/run first.",
        )
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if tehsil:
        records = [r for r in records if r.get("tehsil") == tehsil]

    return {
        "status": "success",
        "count": len(records),
        "parcels": records,
    }


@router.get("/stage4/parcels/{parcel_id}")
def get_parcel_by_id(parcel_id: str):
    """Retrieve a single consolidated parcel record with complete conflict lineage and provenance."""
    json_path = Path(config.STAGE4_CONSOLIDATED_JSON_PATH)
    if not json_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage 4 consolidated output not generated yet. Trigger /api/stage4/run first.",
        )
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    for rec in records:
        if rec.get("parcel_id") == parcel_id:
            return {"status": "success", "parcel": rec}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Parcel '{parcel_id}' not found in consolidated records.",
    )


# ---------------------------------------------------------------------------
# Geospatial Layer Endpoints (QGIS-like GIS View)
# ---------------------------------------------------------------------------
@router.get("/layers/cadastral")
def get_cadastral_layer():
    """Retrieve Cadastral Bhu-Naksha parcels layer GeoJSON."""
    path = Path(config.CADASTRAL_DATA_PATH)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Cadastral data not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/layers/municipal")
def get_municipal_layer():
    """Retrieve Municipal building records layer GeoJSON."""
    path = Path(config.MUNICIPAL_DATA_PATH)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Municipal data not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/layers/ai-extracted")
def get_ai_extracted_layer():
    """Retrieve GeoAI-extracted raw structures layer GeoJSON."""
    path = Path(config.AI_EXTRACTED_OUTPUT_PATH)
    if not path.exists():
        raise HTTPException(status_code=404, detail="AI extracted data not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/layers/review-structures")
def get_review_structures_layer():
    """
    Retrieve all structures categorized by their current review state
    (verified, audit_pending, disputed, locked_disputed).
    """
    structures: Dict[str, Dict[str, Any]] = {}

    # 1. GeoAI Stage 3 outputs
    v_path = Path(config.STAGE3_VERIFIED_OUTPUT_PATH)
    if v_path.exists():
        with open(v_path, "r", encoding="utf-8") as f:
            for feat in json.load(f).get("features", []):
                sid = feat.get("properties", {}).get("structure_id")
                if sid:
                    structures[sid] = feat

    p_path = Path(config.STAGE3_AUDIT_PENDING_OUTPUT_PATH)
    if p_path.exists():
        with open(p_path, "r", encoding="utf-8") as f:
            for feat in json.load(f).get("features", []):
                sid = feat.get("properties", {}).get("structure_id")
                if sid:
                    structures[sid] = feat

    d_path = Path(config.STAGE3_DISPUTED_OUTPUT_PATH)
    if d_path.exists():
        with open(d_path, "r", encoding="utf-8") as f:
            for feat in json.load(f).get("features", []):
                sid = feat.get("properties", {}).get("structure_id")
                if sid:
                    structures[sid] = feat

    # 2. Human verification decisions overlay
    h_path = Path(config.HUMAN_VERIFICATION_RECORDS_PATH)
    if h_path.exists():
        with open(h_path, "r", encoding="utf-8") as f:
            for feat in json.load(f).get("features", []):
                sid = feat.get("properties", {}).get("structure_id")
                if sid:
                    structures[sid] = feat

    return {
        "type": "FeatureCollection",
        "name": "review_structures_layer",
        "features": list(structures.values()),
    }

