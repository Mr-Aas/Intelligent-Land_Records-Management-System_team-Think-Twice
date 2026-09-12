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
    "official_alpha": {
        "official_id": "official_alpha",
        "username": "official_alpha",
        "password": "password123",
        "name": "Ramesh Kumar",
        "role": "Lekhpal",
        "tehsil": "Tehsil-Alpha",
        "district": "Synthetic-District",
    },
    "official_beta": {
        "official_id": "official_beta",
        "username": "official_beta",
        "password": "password123",
        "name": "Suresh Singh",
        "role": "Lekhpal",
        "tehsil": "Tehsil-Beta",
        "district": "Synthetic-District",
    },
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
    """Authenticate synthetic official credentials."""
    official = SYNTHETIC_OFFICIALS.get(username)
    if official and official["password"] == password:
        # Return official profile without password
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
    Retrieve audit_pending and disputed structures filtered by the official's assigned tehsil.

    If include_decided is False (default), records that have already been
    verified or locked_disputed by a human official are excluded from the pending review queue.
    """
    official = get_official(official_id)
    if not official:
        raise ValueError(f"Unknown official: {official_id}")

    target_tehsil = official["tehsil"]

    # Load Stage 3 audit_pending and disputed outputs
    pending_fc = _load_geojson(config.STAGE3_AUDIT_PENDING_OUTPUT_PATH)
    disputed_fc = _load_geojson(config.STAGE3_DISPUTED_OUTPUT_PATH)

    # Load any recorded human decisions
    human_fc = _load_geojson(config.HUMAN_VERIFICATION_RECORDS_PATH)
    decided_by_id = {
        f["properties"].get("structure_id"): f
        for f in human_fc.get("features", [])
        if "properties" in f and "structure_id" in f["properties"]
    }

    # Combined candidate pool
    all_features: Dict[str, Dict[str, Any]] = {}
    for feat in pending_fc.get("features", []):
        sid = feat.get("properties", {}).get("structure_id")
        if sid:
            all_features[sid] = feat
    for feat in disputed_fc.get("features", []):
        sid = feat.get("properties", {}).get("structure_id")
        if sid:
            all_features[sid] = feat

    # Overlay human decisions
    for sid, decided_feat in decided_by_id.items():
        all_features[sid] = decided_feat

    # Filter strictly by the official's assigned tehsil
    queue: List[Dict[str, Any]] = []
    for sid, feat in all_features.items():
        feat_tehsil = _get_structure_tehsil(feat)
        if feat_tehsil != target_tehsil:
            continue

        status = feat.get("properties", {}).get("status")
        if not include_decided:
            # Only include records currently in review states
            if status in ("audit_pending", "disputed"):
                queue.append(feat)
        else:
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
        "tehsil": official["tehsil"],
        "previous_status": old_status,
        "new_status": "locked_disputed",
        "timestamp": timestamp_iso,
        "notes": notes,
    }
    _append_audit_log(audit_entry, config.HUMAN_AUDIT_LOG_PATH)

    return feature
