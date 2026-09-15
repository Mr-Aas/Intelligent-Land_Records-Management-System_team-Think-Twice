"""
GeoServer OGC WMS/WFS Automated Configuration Service (§14, §15).

Provides REST API automation for setting up GeoServer workspaces, PostGIS datastores,
and publishing spatial layers over Web Map Service (WMS) and Web Feature Service (WFS).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

# GeoServer Configuration Defaults
GEOSERVER_URL = os.getenv("GEOSERVER_URL", "http://localhost:8080/geoserver")
GEOSERVER_USER = os.getenv("GEOSERVER_ADMIN_USER", "admin")
GEOSERVER_PASS = os.getenv("GEOSERVER_ADMIN_PASSWORD", "geoserver")
WORKSPACE_NAME = "gis_autopilot"
DATASTORE_NAME = "postgis_store"

SPATIAL_TABLES = [
    "cadastral_parcels",
    "municipal_buildings",
    "ai_extracted_structures",
    "structure_verifications",
    "consolidated_parcels",
]


def check_geoserver_status() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Check if GeoServer service is reachable on port 8080.

    Returns:
        (is_online: bool, status_message: str, capabilities_urls: dict)
    """
    try:
        resp = requests.get(f"{GEOSERVER_URL}/rest/workspaces.json", auth=(GEOSERVER_USER, GEOSERVER_PASS), timeout=3)
        if resp.status_code in [200, 401]:
            capabilities = {
                "workspace": WORKSPACE_NAME,
                "wms_capabilities": f"{GEOSERVER_URL}/{WORKSPACE_NAME}/wms?service=WMS&version=1.1.1&request=GetCapabilities",
                "wfs_capabilities": f"{GEOSERVER_URL}/{WORKSPACE_NAME}/wfs?service=WFS&version=1.1.0&request=GetCapabilities",
            }
            return True, "GeoServer REST service is online.", capabilities
        return False, f"GeoServer returned status code {resp.status_code}", None
    except Exception as e:
        return False, f"GeoServer offline or unreachable: {str(e)}", None


def setup_geoserver() -> Dict[str, Any]:
    """
    Automate GeoServer workspace, PostGIS datastore connection, and layer publishing.

    Returns:
        Summary of published layers and status.
    """
    is_online, msg, caps = check_geoserver_status()
    if not is_online:
        return {
            "status": "warning",
            "message": f"GeoServer service is not currently running. Start GeoServer container via docker-compose up geoserver. Details: {msg}",
            "workspace": WORKSPACE_NAME,
            "published_layers": [],
        }

    auth = (GEOSERVER_USER, GEOSERVER_PASS)
    headers = {"Content-Type": "application/json"}
    published = []

    try:
        # 1. Create Workspace
        ws_url = f"{GEOSERVER_URL}/rest/workspaces"
        ws_payload = {"workspace": {"name": WORKSPACE_NAME}}
        requests.post(ws_url, json=ws_payload, auth=auth, headers=headers)

        # 2. Create PostGIS DataStore
        ds_url = f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE_NAME}/datastores"
        ds_payload = {
            "dataStore": {
                "name": DATASTORE_NAME,
                "connectionParameters": {
                    "entry": [
                        {"@key": "dbtype", "$": "postgis"},
                        {"@key": "host", "$": os.getenv("POSTGRES_HOST", "localhost")},
                        {"@key": "port", "$": "5432"},
                        {"@key": "database", "$": "land_geospatial_db"},
                        {"@key": "schema", "$": "public"},
                        {"@key": "user", "$": "postgres"},
                        {"@key": "passwd", "$": "postgres_password"},
                        {"@key": "Expose primary keys", "$": "true"},
                    ]
                },
            }
        }
        requests.post(ds_url, json=ds_payload, auth=auth, headers=headers)

        # 3. Publish Spatial Layer FeatureTypes
        for table in SPATIAL_TABLES:
            ft_url = f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE_NAME}/datastores/{DATASTORE_NAME}/featuretypes"
            ft_payload = {
                "featureType": {
                    "name": table,
                    "nativeName": table,
                    "title": table.replace("_", " ").title(),
                    "srs": "EPSG:4326",
                    "nativeCRS": "EPSG:4326",
                }
            }
            resp = requests.post(ft_url, json=ft_payload, auth=auth, headers=headers)
            if resp.status_code in [201, 200, 409]:
                published.append(f"{WORKSPACE_NAME}:{table}")

        return {
            "status": "success",
            "message": f"GeoServer workspace '{WORKSPACE_NAME}' and {len(published)} PostGIS layers published.",
            "workspace": WORKSPACE_NAME,
            "datastore": DATASTORE_NAME,
            "published_layers": published,
            "capabilities": caps,
        }

    except Exception as e:
        logger.error("Error during GeoServer setup: %s", e)
        return {
            "status": "error",
            "message": f"GeoServer configuration error: {str(e)}",
            "workspace": WORKSPACE_NAME,
            "published_layers": published,
        }
