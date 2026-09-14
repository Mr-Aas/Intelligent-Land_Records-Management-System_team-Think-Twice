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
from app.db import session as db_session
from app.db import sync as db_sync
from app.geoserver import setup as gs_setup
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform as shapely_transform

router = APIRouter(prefix="/api")

_wgs84_transformer = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)


def _ensure_wgs84_feature(feat: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure geometry coordinates are in standard WGS84 (EPSG:4326) for Leaflet rendering."""
    if not feat or "geometry" not in feat or not feat["geometry"]:
        return feat
    try:
        geom = shape(feat["geometry"])
        if geom.is_empty:
            return feat
        coords = None
        if geom.geom_type == "Polygon":
            coords = list(geom.exterior.coords)
        elif geom.geom_type == "MultiPolygon" and len(geom.geoms) > 0:
            coords = list(geom.geoms[0].exterior.coords)
        if coords and (abs(coords[0][0]) > 180 or abs(coords[0][1]) > 90):
            wgs_geom = shapely_transform(_wgs84_transformer.transform, geom)
            feat = dict(feat)
            feat["geometry"] = mapping(wgs_geom)
    except Exception:
        pass
    return feat



# ---------------------------------------------------------------------------
# Database & PostGIS Management Endpoints (§12)
# ---------------------------------------------------------------------------
@router.get("/db/status")
def get_db_status():
    """Check PostgreSQL connection, PostGIS extension status, and table record metrics."""
    connected, message = db_session.check_db_connection()
    postgis_version = db_session.get_postgis_version() if connected else None

    table_counts = {}
    if connected:
        try:
            from app.db.models import (
                CadastralParcelDB,
                MunicipalBuildingDB,
                AIExtractedStructureDB,
                StructureVerificationDB,
                HumanAuditLogDB,
                OfficialDB,
                ConsolidatedParcelDB,
            )
            SessionLocal = db_session.get_session_factory()
            db = SessionLocal()
            table_counts = {
                "cadastral_parcels": db.query(CadastralParcelDB).count(),
                "municipal_buildings": db.query(MunicipalBuildingDB).count(),
                "ai_extracted_structures": db.query(AIExtractedStructureDB).count(),
                "structure_verifications": db.query(StructureVerificationDB).count(),
                "human_audit_log": db.query(HumanAuditLogDB).count(),
                "officials": db.query(OfficialDB).count(),
                "consolidated_parcels": db.query(ConsolidatedParcelDB).count(),
            }
            db.close()
        except Exception as e:
            table_counts = {"error": str(e)}

    return {
        "status": "online" if connected else "offline",
        "database_url": config.DATABASE_URL.split("@")[-1] if "@" in config.DATABASE_URL else config.DATABASE_URL,
        "connected": connected,
        "message": message,
        "postgis_enabled": postgis_version is not None,
        "postgis_version": postgis_version,
        "table_counts": table_counts,
    }


@router.post("/db/sync")
def trigger_db_sync():
    """Trigger PostGIS database table creation and pipeline data synchronization."""
    result = db_sync.sync_all_to_db()
    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Database synchronization failed."),
        )
    return result


# ---------------------------------------------------------------------------
# GeoServer OGC WMS/WFS Management Endpoints (§14, §15)
# ---------------------------------------------------------------------------
@router.get("/geoserver/status")
def get_geoserver_status():
    """Check GeoServer container readiness and OGC capabilities URLs."""
    is_online, message, capabilities = gs_setup.check_geoserver_status()
    return {
        "status": "online" if is_online else "offline",
        "message": message,
        "capabilities": capabilities,
    }


@router.post("/geoserver/setup")
def trigger_geoserver_setup():
    """Trigger automated GeoServer REST configuration, workspace, datastore, and layer publishing."""
    result = gs_setup.setup_geoserver()
    return result


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., description="username (e.g. 'official_ramesh')")
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
    - `forward_to_revenue`: Lekhpal forwards to Revenue Inspector.
    - `forward_to_tehsildar`: Revenue Inspector forwards to Tehsildar.
    - `tehsildar_commit`: Tehsildar commits final approval to PostGIS DB.
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
        elif payload.action == "forward_to_revenue":
            feature = hv_service.forward_to_revenue(
                structure_id=payload.structure_id,
                official_id=payload.official_id,
                notes=payload.notes,
            )
        elif payload.action == "forward_to_tehsildar":
            feature = hv_service.forward_to_tehsildar(
                structure_id=payload.structure_id,
                official_id=payload.official_id,
                notes=payload.notes,
            )
        elif payload.action == "tehsildar_commit":
            feature = hv_service.tehsildar_commit(
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
def get_audit_log(
    official_id: Optional[str] = Query(None, description="Filter audit logs by official's assigned tehsil")
):
    """Retrieve append-only audit trail of human actions (filtered by official's tehsil if official_id is provided)."""
    path = Path(config.HUMAN_AUDIT_LOG_PATH)
    if not path.exists():
        return {"status": "success", "count": 0, "entries": []}
    with open(path, "r", encoding="utf-8") as f:
        try:
            entries = json.load(f)
        except json.JSONDecodeError:
            entries = []

    if official_id:
        official = hv_service.get_official(official_id)
        if official and official.get("tehsil"):
            tehsil = official["tehsil"]
            entries = [e for e in entries if e.get("tehsil") == tehsil]

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

    normalized_features = [_ensure_wgs84_feature(feat) for feat in structures.values()]

    return {
        "type": "FeatureCollection",
        "name": "review_structures_layer",
        "features": normalized_features,
    }

