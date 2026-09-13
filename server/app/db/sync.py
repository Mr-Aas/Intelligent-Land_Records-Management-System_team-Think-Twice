"""
Database Initialization & GeoJSON/Pipeline Data Synchronization for PostGIS (§12).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.db.models import (
    AIExtractedStructureDB,
    CadastralParcelDB,
    ConsolidatedParcelDB,
    HumanAuditLogDB,
    MunicipalBuildingDB,
    OfficialDB,
    StructureVerificationDB,
)
from app.db.session import Base, get_engine, get_session_factory
from app.pipeline import config
from geoalchemy2.elements import WKTElement
from shapely.geometry import shape
from sqlalchemy import text

logger = logging.getLogger(__name__)


def init_db() -> bool:
    """
    Enable PostGIS extension and create database tables with spatial indexes.

    Returns:
        True if initialization succeeded, False otherwise.
    """
    try:
        engine = get_engine()

        # 1. Enable PostGIS extension
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            logger.info("PostGIS extension initialized.")

        # 2. Create tables & indexes
        Base.metadata.create_all(bind=engine)
        logger.info("Database spatial tables and indexes created successfully.")
        return True
    except Exception as e:
        logger.error("Failed to initialize PostGIS database: %s", e)
        return False


def _geojson_to_wkt(geometry_dict: Optional[Dict[str, Any]]) -> Optional[WKTElement]:
    """Convert GeoJSON geometry dict to GeoAlchemy2 WKTElement with SRID 4326."""
    if not geometry_dict:
        return None
    try:
        geom_obj = shape(geometry_dict)
        if geom_obj.is_empty:
            return None
        return WKTElement(geom_obj.wkt, srid=4326)
    except Exception as e:
        logger.warning("Could not convert geometry to WKT: %s", e)
        return None


def sync_all_to_db() -> Dict[str, Any]:
    """
    Synchronize all raw layers, pipeline outputs, official accounts,
    human audit logs, and Stage 4 consolidated records into PostgreSQL/PostGIS.

    Returns:
        Summary of inserted/updated record counts per table.
    """
    if not init_db():
        return {"status": "error", "message": "Database initialization failed."}

    SessionLocal = get_session_factory()
    db = SessionLocal()
    counts = {}

    try:
        # 1. Sync Synthetic Officials
        officials_data = [
          {
            "official_id": "official_alpha",
            "username": "ramesh_alpha",
            "password_hash": "lekhpal123",
            "name": "Ramesh Kumar",
            "role": "Lekhpal",
            "tehsil": "Tehsil-Alpha",
            "district": "Kumaon District",
          },
          {
            "official_id": "official_beta",
            "username": "suresh_beta",
            "password_hash": "lekhpal123",
            "name": "Suresh Singh",
            "role": "Lekhpal",
            "tehsil": "Tehsil-Beta",
            "district": "Kumaon District",
          },
        ]
        db.query(OfficialDB).delete()
        for off in officials_data:
            db.add(OfficialDB(**off))
        db.commit()
        counts["officials"] = len(officials_data)

        # 2. Sync Cadastral Parcels
        cad_path = Path(config.CADASTRAL_DATA_PATH)
        if cad_path.exists():
            with open(cad_path, "r", encoding="utf-8") as f:
                features = json.load(f).get("features", [])
            db.query(CadastralParcelDB).delete()
            for feat in features:
                p = feat.get("properties", {})
                wkt = _geojson_to_wkt(feat.get("geometry"))
                db.add(
                    CadastralParcelDB(
                        parcel_id=p.get("parcel_id"),
                        khasra_no=p.get("khasra_no", "N/A"),
                        khata_no=p.get("khata_no", "N/A"),
                        tehsil=p.get("tehsil", "Tehsil-Alpha"),
                        district=p.get("district", "Kumaon District"),
                        land_use=p.get("land_use"),
                        record_area_sqm=p.get("record_area_sqm"),
                        geom=wkt,
                        properties=p,
                    )
                )
            db.commit()
            counts["cadastral_parcels"] = len(features)

        # 3. Sync Municipal Buildings
        mun_path = Path(config.MUNICIPAL_DATA_PATH)
        if mun_path.exists():
            with open(mun_path, "r", encoding="utf-8") as f:
                features = json.load(f).get("features", [])
            db.query(MunicipalBuildingDB).delete()
            for feat in features:
                p = feat.get("properties", {})
                wkt = _geojson_to_wkt(feat.get("geometry"))
                db.add(
                    MunicipalBuildingDB(
                        municipal_building_id=p.get("municipal_building_id"),
                        tehsil=p.get("tehsil"),
                        building_status=p.get("building_status", "registered"),
                        geom=wkt,
                        properties=p,
                    )
                )
            db.commit()
            counts["municipal_buildings"] = len(features)

        # 4. Sync AI Extracted Structures
        ai_path = Path(config.AI_EXTRACTED_OUTPUT_PATH)
        if ai_path.exists():
            with open(ai_path, "r", encoding="utf-8") as f:
                features = json.load(f).get("features", [])
            db.query(AIExtractedStructureDB).delete()
            for feat in features:
                p = feat.get("properties", {})
                wkt = _geojson_to_wkt(feat.get("geometry"))
                db.add(
                    AIExtractedStructureDB(
                        structure_id=p.get("structure_id"),
                        class_name=p.get("class", "building"),
                        confidence=p.get("confidence"),
                        source_tile=p.get("source_tile"),
                        geom=wkt,
                        properties=p,
                    )
                )
            db.commit()
            counts["ai_extracted_structures"] = len(features)

        # 5. Sync Structure Verifications (Stage 3 + Human Overlay)
        structures_map = {}
        for path_str in [
            config.STAGE3_VERIFIED_OUTPUT_PATH,
            config.STAGE3_AUDIT_PENDING_OUTPUT_PATH,
            config.STAGE3_DISPUTED_OUTPUT_PATH,
            config.HUMAN_VERIFICATION_RECORDS_PATH,
        ]:
            p_obj = Path(path_str)
            if p_obj.exists():
                with open(p_obj, "r", encoding="utf-8") as f:
                    for feat in json.load(f).get("features", []):
                        sid = feat.get("properties", {}).get("structure_id")
                        if sid:
                            structures_map[sid] = feat

        db.query(StructureVerificationDB).delete()
        for sid, feat in structures_map.items():
            p = feat.get("properties", {})
            wkt = _geojson_to_wkt(feat.get("geometry"))
            tehsil_val = p.get("tehsil") or (p.get("cadastral_record", {}) or {}).get("tehsil")
            db.add(
                StructureVerificationDB(
                    structure_id=sid,
                    status=p.get("status", "audit_pending"),
                    verification_method=p.get("verification_method", "geoai"),
                    parcel_id=p.get("parcel_id"),
                    overflow_measure=p.get("overflow_measure"),
                    threshold=p.get("configured_threshold"),
                    reason=p.get("reason"),
                    tehsil=tehsil_val,
                    geom=wkt,
                    properties=p,
                )
            )
        db.commit()
        counts["structure_verifications"] = len(structures_map)

        # 6. Sync Human Audit Logs
        log_path = Path(config.HUMAN_AUDIT_LOG_PATH)
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                try:
                    entries = json.load(f)
                except json.JSONDecodeError:
                    entries = []
            db.query(HumanAuditLogDB).delete()
            for e in entries:
                db.add(
                    HumanAuditLogDB(
                        event_id=e.get("event_id"),
                        structure_id=e.get("structure_id"),
                        official_id=e.get("official_id"),
                        official_name=e.get("official_name", "Official"),
                        tehsil=e.get("tehsil", "Tehsil-Alpha"),
                        action=e.get("action"),
                        previous_status=e.get("previous_status"),
                        new_status=e.get("new_status"),
                        notes=e.get("notes"),
                    )
                )
            db.commit()
            counts["human_audit_log"] = len(entries)

        # 7. Sync Stage 4 Consolidated Single Source of Truth Parcels
        s4_json_path = Path(config.STAGE4_CONSOLIDATED_JSON_PATH)
        s4_geojson_path = Path(config.STAGE4_CONSOLIDATED_GEOJSON_PATH)
        if s4_json_path.exists():
            with open(s4_json_path, "r", encoding="utf-8") as f:
                parcels_list = json.load(f)
            geom_map = {}
            if s4_geojson_path.exists():
                with open(s4_geojson_path, "r", encoding="utf-8") as f:
                    for feat in json.load(f).get("features", []):
                        pid = feat.get("properties", {}).get("parcel_id")
                        if pid:
                            geom_map[pid] = feat.get("geometry")

            db.query(ConsolidatedParcelDB).delete()
            for rec in parcels_list:
                pid = rec.get("parcel_id")
                wkt = _geojson_to_wkt(geom_map.get(pid))
                db.add(
                    ConsolidatedParcelDB(
                        parcel_id=pid,
                        khasra_no=rec.get("khasra_no", "N/A"),
                        khata_no=rec.get("khata_no", "N/A"),
                        tehsil=rec.get("tehsil", "Tehsil-Alpha"),
                        district=rec.get("district", "Kumaon District"),
                        resolved_owner=rec.get("resolved_owner", "N/A"),
                        resolved_land_use=rec.get("resolved_land_use", "N/A"),
                        resolved_area_sqm=float(rec.get("resolved_area_sqm", 0.0)),
                        conflict_summary=rec.get("conflict_summary"),
                        source_provenance=rec.get("source_provenance"),
                        department_records=rec.get("department_records"),
                        geom=wkt,
                    )
                )
            db.commit()
            counts["consolidated_parcels"] = len(parcels_list)

        logger.info("Synchronized data into PostGIS database: %s", counts)
        return {
            "status": "success",
            "message": "All pipeline layers and records synchronized to PostGIS database.",
            "counts": counts,
        }

    except Exception as e:
        db.rollback()
        logger.error("Failed during database sync: %s", e)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
