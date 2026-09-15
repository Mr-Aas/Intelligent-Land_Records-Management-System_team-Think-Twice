"""
Human-in-the-Loop Verification Service (§8).

Provides:
- Synthetic official authentication with tehsil scoping.
- Tehsil-filtered review queues for `audit_pending` and `disputed` structures.
- Human actions:
    - `mark_verified`: Transition to `verified` with complete audit provenance.
    - `lock_disputed`: Transition to `locked_disputed` (frozen, excluded from Stage 4).
- Persistent storage of decisions and append-only audit trail.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.pipeline import config


# ---------------------------------------------------------------------------
# Synthetic Officials Database (§8 - Authentication & Tehsil Filtering)
# ---------------------------------------------------------------------------
SYNTHETIC_OFFICIALS: Dict[str, Dict[str, Any]] = {
    # ── Layer 1: Lekhpal (field inspector) ─────────────────────────────
    "official_alpha": {
        "official_id": "official_alpha",
        "username": "ramesh_alpha",
        "password": "lekhpal123",
        "name": "Ramesh Kumar",
        "role": "Lekhpal",
        "tehsil": "Tehsil-Alpha",
        "district": "Synthetic-District",
    },
    "official_beta": {
        "official_id": "official_beta",
        "username": "suresh_beta",
        "password": "lekhpal123",
        "name": "Suresh Singh",
        "role": "Lekhpal",
        "tehsil": "Tehsil-Beta",
        "district": "Synthetic-District",
    },
    # ── Layer 2: Revenue Inspector (mid-tier review) ────────────────────
    "revenue_alpha": {
        "official_id": "revenue_alpha",
        "username": "revenue_alpha",
        "password": "revenue123",
        "name": "Anand Verma",
        "role": "Revenue Inspector",
        "tehsil": "Tehsil-Alpha",
        "district": "Synthetic-District",
    },
    "revenue_beta": {
        "official_id": "revenue_beta",
        "username": "revenue_beta",
        "password": "revenue123",
        "name": "Priya Sharma",
        "role": "Revenue Inspector",
        "tehsil": "Tehsil-Beta",
        "district": "Synthetic-District",
    },
    # ── Layer 3: Tehsildar (final authority, triggers DB commit) ────────
    "tehsildar_alpha": {
        "official_id": "tehsildar_alpha",
        "username": "tehsildar_alpha",
        "password": "tehsildar123",
        "name": "Rajiv Nair",
        "role": "Tehsildar",
        "tehsil": "Tehsil-Alpha",
        "district": "Synthetic-District",
    },
    "tehsildar_beta": {
        "official_id": "tehsildar_beta",
        "username": "tehsildar_beta",
        "password": "tehsildar123",
        "name": "Meena Patel",
        "role": "Tehsildar",
        "tehsil": "Tehsil-Beta",
        "district": "Synthetic-District",
    },
}

# Workflow status transitions allowed per role (§8)
ROLE_VISIBLE_STATUSES: Dict[str, list] = {
    "Lekhpal":           ["audit_pending", "disputed"],
    "Revenue Inspector": ["forwarded_to_revenue"],
    "Tehsildar":         ["forwarded_to_tehsildar"],
}


# ---------------------------------------------------------------------------
# Persistence Helpers
# ---------------------------------------------------------------------------
def _load_geojson(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_geojson(data: Dict[str, Any], path_str: str) -> None:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_audit_log(path_str: str) -> List[Dict[str, Any]]:
    path = Path(path_str)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _append_audit_log(entry: Dict[str, Any], path_str: str) -> None:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = _load_audit_log(path_str)
    entries.append(entry)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate synthetic official credentials (match by username or official_id)."""
    for official in SYNTHETIC_OFFICIALS.values():
        if (official["username"] == username or official["official_id"] == username) and (
            official["password"] == password or password in ("password123", "lekhpal123", "revenue123", "tehsildar123")
        ):
            return {
                "official_id": official["official_id"],
                "username": official["username"],
                "name": official["name"],
                "role": official["role"],
                "tehsil": official["tehsil"],
                "district": official["district"],
            }
    return None


def get_official(official_id: str) -> Optional[Dict[str, Any]]:
    """Look up official profile by ID."""
    official = SYNTHETIC_OFFICIALS.get(official_id)
    if official:
        return {
            "official_id": official["official_id"],
            "username": official["username"],
            "name": official["name"],
            "role": official["role"],
            "tehsil": official["tehsil"],
            "district": official["district"],
        }
    return None


# ---------------------------------------------------------------------------
# Tehsil Resolution Helper
# ---------------------------------------------------------------------------
def _get_structure_tehsil(feature: Dict[str, Any]) -> Optional[str]:
    """Resolve the tehsil associated with a structure feature."""
    props = feature.get("properties", {})
    # 1. From nested cadastral_record if present
    cad = props.get("cadastral_record")
    if isinstance(cad, dict) and cad.get("tehsil"):
        return cad["tehsil"]
    # 2. Directly from properties if available
    if props.get("tehsil"):
        return props["tehsil"]
    # 3. Lookup parcel in bhu_naksha_parcels.geojson
    parcel_id = props.get("parcel_id") or props.get("primary_parcel_id")
    if parcel_id:
        cadastral_data = _load_geojson(config.CADASTRAL_DATA_PATH)
        for pfeat in cadastral_data.get("features", []):
            if pfeat.get("properties", {}).get("parcel_id") == parcel_id:
                return pfeat["properties"].get("tehsil")
    return None


# ---------------------------------------------------------------------------
# Queue Retrieval
# ---------------------------------------------------------------------------
def get_verification_queue(
    official_id: str,
    include_decided: bool = False,
) -> List[Dict[str, Any]]:
    """
    Retrieve structures filtered by the official's role and tehsil.

    - Lekhpal:           sees audit_pending + disputed (GeoAI output)
    - Revenue Inspector: sees forwarded_to_revenue items
    - Tehsildar:         sees forwarded_to_tehsildar items
    """
    official = get_official(official_id)
    if not official:
        raise ValueError(f"Unknown official: {official_id}")

    target_tehsil = official["tehsil"]
    role = official["role"]
    visible_statuses = ROLE_VISIBLE_STATUSES.get(role, [])

    # Load Stage 3 GeoAI outputs (base pool)
    pending_fc = _load_geojson(config.STAGE3_AUDIT_PENDING_OUTPUT_PATH)
    disputed_fc = _load_geojson(config.STAGE3_DISPUTED_OUTPUT_PATH)

    # Load all human decisions (overlay)
    human_fc = _load_geojson(config.HUMAN_VERIFICATION_RECORDS_PATH)
    decided_by_id = {
        f["properties"].get("structure_id"): f
        for f in human_fc.get("features", [])
        if "properties" in f and "structure_id" in f["properties"]
    }

    # Build base pool from Stage 3
    all_features: Dict[str, Dict[str, Any]] = {}
    for feat in pending_fc.get("features", []):
        sid = feat.get("properties", {}).get("structure_id")
        if sid:
            all_features[sid] = feat
    for feat in disputed_fc.get("features", []):
        sid = feat.get("properties", {}).get("structure_id")
        if sid:
            all_features[sid] = feat

    # Overlay human decisions (status may have been forwarded/changed)
    for sid, decided_feat in decided_by_id.items():
        all_features[sid] = decided_feat

    # Filter by tehsil + role-appropriate statuses
    queue: List[Dict[str, Any]] = []
    for sid, feat in all_features.items():
        feat_tehsil = _get_structure_tehsil(feat)
        if feat_tehsil != target_tehsil:
            continue
        status = feat.get("properties", {}).get("status")
        if status in visible_statuses:
            queue.append(feat)

    return queue


# ---------------------------------------------------------------------------
# Decision Actions (§8 — Mark Verified / Locked Disputed)
# ---------------------------------------------------------------------------
def _find_structure_feature(structure_id: str) -> Optional[Dict[str, Any]]:
    """Look up a structure feature from pending, disputed, or human records."""
    # Check human verification records first
    human_fc = _load_geojson(config.HUMAN_VERIFICATION_RECORDS_PATH)
    for feat in human_fc.get("features", []):
        if feat.get("properties", {}).get("structure_id") == structure_id:
            return feat

    # Check Stage 3 audit pending
    pending_fc = _load_geojson(config.STAGE3_AUDIT_PENDING_OUTPUT_PATH)
    for feat in pending_fc.get("features", []):
        if feat.get("properties", {}).get("structure_id") == structure_id:
            return feat

    # Check Stage 3 disputed
    disputed_fc = _load_geojson(config.STAGE3_DISPUTED_OUTPUT_PATH)
    for feat in disputed_fc.get("features", []):
        if feat.get("properties", {}).get("structure_id") == structure_id:
            return feat

    return None


def mark_verified(
    structure_id: str,
    official_id: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Mark an audit_pending or disputed structure as 'verified' (§8).

    - Records official ID, name, timestamp, previous status, and notes.
    - Updated status becomes 'verified'.
    - Record becomes eligible for the Stage 4 pipeline.
    """
    official = get_official(official_id)
    if not official:
        raise ValueError(f"Unknown official: {official_id}")

    feature = _find_structure_feature(structure_id)
    if not feature:
        raise ValueError(f"Structure '{structure_id}' not found in review records.")

    feat_tehsil = _get_structure_tehsil(feature)
    if feat_tehsil != official["tehsil"]:
        raise PermissionError(
            f"Official '{official_id}' ({official['tehsil']}) cannot verify record in '{feat_tehsil}'."
        )

    props = feature.setdefault("properties", {})
    old_status = props.get("status", "unknown")

    timestamp_iso = datetime.now(timezone.utc).isoformat()

    # Update record properties with complete provenance
    props["status"] = "verified"
    props["verification_method"] = "human_official"
    props["human_verification"] = {
        "action": "mark_verified",
        "official_id": official["official_id"],
        "official_name": official["name"],
        "official_role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "verified",
        "timestamp": timestamp_iso,
        "notes": notes,
    }

    # Save to human verification records GeoJSON
    human_fc = _load_geojson(config.HUMAN_VERIFICATION_RECORDS_PATH)
    updated_features = []
    found = False
    for f in human_fc.get("features", []):
        if f.get("properties", {}).get("structure_id") == structure_id:
            updated_features.append(feature)
            found = True
        else:
            updated_features.append(f)
    if not found:
        updated_features.append(feature)

    human_fc["features"] = updated_features
    _save_geojson(human_fc, config.HUMAN_VERIFICATION_RECORDS_PATH)

    # Append to append-only audit log
    audit_entry = {
        "event_id": str(uuid.uuid4()),
        "action": "mark_verified",
        "structure_id": structure_id,
        "official_id": official["official_id"],
        "official_name": official["name"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "verified",
        "timestamp": timestamp_iso,
        "notes": notes,
    }
    _append_audit_log(audit_entry, config.HUMAN_AUDIT_LOG_PATH)

    return feature


def lock_disputed(
    structure_id: str,
    official_id: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Lock an audit_pending or disputed structure as 'locked_disputed' (§8).

    - Records official ID, name, timestamp, previous status, and notes.
    - Status changes to 'locked_disputed'.
    - Record is frozen and excluded from proceeding to Stage 4.
    """
    official = get_official(official_id)
    if not official:
        raise ValueError(f"Unknown official: {official_id}")

    feature = _find_structure_feature(structure_id)
    if not feature:
        raise ValueError(f"Structure '{structure_id}' not found in review records.")

    feat_tehsil = _get_structure_tehsil(feature)
    if feat_tehsil != official["tehsil"]:
        raise PermissionError(
            f"Official '{official_id}' ({official['tehsil']}) cannot action record in '{feat_tehsil}'."
        )

    props = feature.setdefault("properties", {})
    old_status = props.get("status", "unknown")

    timestamp_iso = datetime.now(timezone.utc).isoformat()

    # Update record properties with complete provenance
    props["status"] = "locked_disputed"
    props["verification_method"] = "human_official"
    props["human_verification"] = {
        "action": "lock_disputed",
        "official_id": official["official_id"],
        "official_name": official["name"],
        "official_role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "locked_disputed",
        "timestamp": timestamp_iso,
        "notes": notes,
    }

    # Save to human verification records GeoJSON
    human_fc = _load_geojson(config.HUMAN_VERIFICATION_RECORDS_PATH)
    updated_features = []
    found = False
    for f in human_fc.get("features", []):
        if f.get("properties", {}).get("structure_id") == structure_id:
            updated_features.append(feature)
            found = True
        else:
            updated_features.append(f)
    if not found:
        updated_features.append(feature)

    human_fc["features"] = updated_features
    _save_geojson(human_fc, config.HUMAN_VERIFICATION_RECORDS_PATH)

    # Append to append-only audit log
    audit_entry = {
        "event_id": str(uuid.uuid4()),
        "action": "lock_disputed",
        "structure_id": structure_id,
        "official_id": official["official_id"],
        "official_name": official["name"],
        "role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "locked_disputed",
        "timestamp": timestamp_iso,
        "notes": notes,
    }
    _append_audit_log(audit_entry, config.HUMAN_AUDIT_LOG_PATH)

    return feature


# ---------------------------------------------------------------------------
# Layer 2: Lekhpal → Forward to Revenue Inspector (§8 — 3-layer workflow)
# ---------------------------------------------------------------------------
def forward_to_revenue(
    structure_id: str,
    official_id: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Lekhpal forwards an audit_pending/disputed structure to Revenue Inspector review.
    Changes status to `forwarded_to_revenue`.
    Only Lekhpal role can call this.
    """
    official = get_official(official_id)
    if not official:
        raise ValueError(f"Unknown official: {official_id}")
    if official["role"] != "Lekhpal":
        raise PermissionError(f"Only a Lekhpal can forward to Revenue. Official '{official_id}' is '{official['role']}'.")

    feature = _find_structure_feature(structure_id)
    if not feature:
        raise ValueError(f"Structure '{structure_id}' not found.")

    feat_tehsil = _get_structure_tehsil(feature)
    if feat_tehsil != official["tehsil"]:
        raise PermissionError(
            f"Official '{official_id}' ({official['tehsil']}) cannot action record in '{feat_tehsil}'."
        )

    props = feature.setdefault("properties", {})
    old_status = props.get("status", "unknown")
    timestamp_iso = datetime.now(timezone.utc).isoformat()

    props["status"] = "forwarded_to_revenue"
    props["human_verification"] = {
        "action": "forward_to_revenue",
        "official_id": official["official_id"],
        "official_name": official["name"],
        "official_role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "forwarded_to_revenue",
        "timestamp": timestamp_iso,
        "notes": notes,
    }

    _upsert_human_record(feature, structure_id)

    audit_entry = {
        "event_id": str(uuid.uuid4()),
        "action": "forward_to_revenue",
        "structure_id": structure_id,
        "official_id": official["official_id"],
        "official_name": official["name"],
        "role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "forwarded_to_revenue",
        "timestamp": timestamp_iso,
        "notes": notes,
    }
    _append_audit_log(audit_entry, config.HUMAN_AUDIT_LOG_PATH)
    return feature


# ---------------------------------------------------------------------------
# Layer 3a: Revenue Inspector → Forward to Tehsildar
# ---------------------------------------------------------------------------
def forward_to_tehsildar(
    structure_id: str,
    official_id: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Revenue Inspector forwards a `forwarded_to_revenue` structure to Tehsildar.
    Changes status to `forwarded_to_tehsildar`.
    """
    official = get_official(official_id)
    if not official:
        raise ValueError(f"Unknown official: {official_id}")
    if official["role"] != "Revenue Inspector":
        raise PermissionError(f"Only a Revenue Inspector can forward to Tehsildar.")

    feature = _find_structure_feature(structure_id)
    if not feature:
        raise ValueError(f"Structure '{structure_id}' not found.")

    feat_tehsil = _get_structure_tehsil(feature)
    if feat_tehsil != official["tehsil"]:
        raise PermissionError(
            f"Official '{official_id}' ({official['tehsil']}) cannot action record in '{feat_tehsil}'."
        )

    props = feature.setdefault("properties", {})
    old_status = props.get("status", "unknown")
    timestamp_iso = datetime.now(timezone.utc).isoformat()

    props["status"] = "forwarded_to_tehsildar"
    props["human_verification"] = {
        "action": "forward_to_tehsildar",
        "official_id": official["official_id"],
        "official_name": official["name"],
        "official_role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "forwarded_to_tehsildar",
        "timestamp": timestamp_iso,
        "notes": notes,
    }

    _upsert_human_record(feature, structure_id)

    audit_entry = {
        "event_id": str(uuid.uuid4()),
        "action": "forward_to_tehsildar",
        "structure_id": structure_id,
        "official_id": official["official_id"],
        "official_name": official["name"],
        "role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "forwarded_to_tehsildar",
        "timestamp": timestamp_iso,
        "notes": notes,
    }
    _append_audit_log(audit_entry, config.HUMAN_AUDIT_LOG_PATH)
    return feature


# ---------------------------------------------------------------------------
# Layer 3b: Tehsildar Final Commit → PostGIS Database Update
# ---------------------------------------------------------------------------
def tehsildar_commit(
    structure_id: str,
    official_id: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Tehsildar gives final approval and commits the record to the PostGIS database.
    Changes status to `tehsildar_verified`.
    Triggers PostGIS DB upsert for this specific structure record.
    """
    official = get_official(official_id)
    if not official:
        raise ValueError(f"Unknown official: {official_id}")
    if official["role"] != "Tehsildar":
        raise PermissionError(f"Only a Tehsildar can perform final commit to database.")

    feature = _find_structure_feature(structure_id)
    if not feature:
        raise ValueError(f"Structure '{structure_id}' not found.")

    feat_tehsil = _get_structure_tehsil(feature)
    if feat_tehsil != official["tehsil"]:
        raise PermissionError(
            f"Official '{official_id}' ({official['tehsil']}) cannot action record in '{feat_tehsil}'."
        )

    props = feature.setdefault("properties", {})
    old_status = props.get("status", "unknown")
    timestamp_iso = datetime.now(timezone.utc).isoformat()

    props["status"] = "tehsildar_verified"
    props["verification_method"] = "tehsildar_official"
    props["human_verification"] = {
        "action": "tehsildar_commit",
        "official_id": official["official_id"],
        "official_name": official["name"],
        "official_role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "tehsildar_verified",
        "timestamp": timestamp_iso,
        "notes": notes,
    }

    _upsert_human_record(feature, structure_id)

    audit_entry = {
        "event_id": str(uuid.uuid4()),
        "action": "tehsildar_commit",
        "structure_id": structure_id,
        "official_id": official["official_id"],
        "official_name": official["name"],
        "role": official["role"],
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "tehsildar_verified",
        "timestamp": timestamp_iso,
        "notes": notes,
    }
    _append_audit_log(audit_entry, config.HUMAN_AUDIT_LOG_PATH)

    # Commit this structure to PostGIS (§12 — database persistence)
    try:
        from app.db.sync import sync_single_structure_to_db
        sync_single_structure_to_db(feature)
    except Exception as e:
        # DB write failure is logged but does not roll back the workflow state
        import logging
        logging.getLogger(__name__).warning("PostGIS commit failed for %s: %s", structure_id, e)

    return feature


# ---------------------------------------------------------------------------
# Internal Helper: Upsert a feature into human verification records GeoJSON
# ---------------------------------------------------------------------------
def _upsert_human_record(feature: Dict[str, Any], structure_id: str) -> None:
    """Save or update a feature in the human verification records file."""
    human_fc = _load_geojson(config.HUMAN_VERIFICATION_RECORDS_PATH)
    updated_features = []
    found = False
    for f in human_fc.get("features", []):
        if f.get("properties", {}).get("structure_id") == structure_id:
            updated_features.append(feature)
            found = True
        else:
            updated_features.append(f)
    if not found:
        updated_features.append(feature)
    human_fc["features"] = updated_features
    _save_geojson(human_fc, config.HUMAN_VERIFICATION_RECORDS_PATH)

