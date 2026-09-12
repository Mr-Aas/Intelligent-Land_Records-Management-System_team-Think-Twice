"""
Unit and Integration Tests for Human Verification & Stage 4 Pipeline (§8, §9, §10, §20).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import config
from app.pipeline.human_verification import service as hv_service
from app.pipeline.stage4 import runner as stage4_runner
from app.pipeline.stage4.resolver import SmartRuleConflictResolver


class TestHumanVerificationAndStage4(unittest.TestCase):
    """Test suite for human-in-the-loop verification and Stage 4 multi-department consolidation."""

    def setUp(self):
        # Create a temporary directory for test output isolation
        self.test_dir = tempfile.mkdtemp()

        # Backup original output paths
        self.orig_hv_records = config.HUMAN_VERIFICATION_RECORDS_PATH
        self.orig_hv_audit = config.HUMAN_AUDIT_LOG_PATH
        self.orig_s4_json = config.STAGE4_CONSOLIDATED_JSON_PATH
        self.orig_s4_geojson = config.STAGE4_CONSOLIDATED_GEOJSON_PATH

        # Redirect to temporary test directory
        config.HUMAN_VERIFICATION_RECORDS_PATH = str(Path(self.test_dir) / "human_verification_records.geojson")
        config.HUMAN_AUDIT_LOG_PATH = str(Path(self.test_dir) / "human_audit_log.json")
        config.STAGE4_CONSOLIDATED_JSON_PATH = str(Path(self.test_dir) / "stage4_consolidated_parcels.json")
        config.STAGE4_CONSOLIDATED_GEOJSON_PATH = str(Path(self.test_dir) / "stage4_consolidated_parcels.geojson")

        self.client = TestClient(app)

    def tearDown(self):
        # Restore original paths
        config.HUMAN_VERIFICATION_RECORDS_PATH = self.orig_hv_records
        config.HUMAN_AUDIT_LOG_PATH = self.orig_hv_audit
        config.STAGE4_CONSOLIDATED_JSON_PATH = self.orig_s4_json
        config.STAGE4_CONSOLIDATED_GEOJSON_PATH = self.orig_s4_geojson

        # Clean up temporary test files
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # 1. Synthetic Officials & Tehsil Scoping (§8)
    # -----------------------------------------------------------------------
    def test_synthetic_official_authentication(self):
        """Verify synthetic credentials authenticate and return tehsil scope."""
        alpha = hv_service.authenticate("official_alpha", "password123")
        self.assertIsNotNone(alpha)
        self.assertEqual(alpha["tehsil"], "Tehsil-Alpha")
        self.assertEqual(alpha["role"], "Lekhpal")

        beta = hv_service.authenticate("official_beta", "password123")
        self.assertIsNotNone(beta)
        self.assertEqual(beta["tehsil"], "Tehsil-Beta")

        invalid = hv_service.authenticate("official_alpha", "wrong_password")
        self.assertIsNone(invalid)

    def test_tehsil_scoped_queue_filtering(self):
        """
        Verify that officials only see records in their assigned tehsil (§8).
        - official_alpha (Tehsil-Alpha) sees STR-007.
        - official_beta (Tehsil-Beta) sees STR-005, STR-006.
        """
        queue_alpha = hv_service.get_verification_queue("official_alpha")
        alpha_ids = [f["properties"]["structure_id"] for f in queue_alpha]
        self.assertIn("STR-007", alpha_ids)
        self.assertNotIn("STR-005", alpha_ids)
        self.assertNotIn("STR-006", alpha_ids)

        queue_beta = hv_service.get_verification_queue("official_beta")
        beta_ids = [f["properties"]["structure_id"] for f in queue_beta]
        self.assertIn("STR-005", beta_ids)
        self.assertIn("STR-006", beta_ids)
        self.assertNotIn("STR-007", beta_ids)

    def test_unauthorized_cross_tehsil_action_rejected(self):
        """Ensure an official cannot action records outside their assigned tehsil."""
        with self.assertRaises(PermissionError):
            # STR-005 is in Tehsil-Beta; official_alpha is in Tehsil-Alpha
            hv_service.mark_verified("STR-005", "official_alpha", "Unauthorized attempt")

    # -----------------------------------------------------------------------
    # 2. Human Actions: Mark Verified & Lock Disputed (§8)
    # -----------------------------------------------------------------------
    def test_mark_verified_action_and_audit_trail(self):
        """Verify mark_verified transitions status to 'verified' and creates audit log entry."""
        result = hv_service.mark_verified(
            structure_id="STR-005",
            official_id="official_beta",
            notes="Field boundary survey confirmed legitimate variance.",
        )
        self.assertEqual(result["properties"]["status"], "verified")
        self.assertEqual(result["properties"]["verification_method"], "human_official")
        self.assertEqual(result["properties"]["human_verification"]["official_id"], "official_beta")
        self.assertEqual(result["properties"]["human_verification"]["previous_status"], "audit_pending")
        self.assertEqual(result["properties"]["human_verification"]["new_status"], "verified")

        # Verify audit log was recorded
        audit_log = hv_service._load_audit_log(config.HUMAN_AUDIT_LOG_PATH)
        self.assertEqual(len(audit_log), 1)
        self.assertEqual(audit_log[0]["action"], "mark_verified")
        self.assertEqual(audit_log[0]["structure_id"], "STR-005")
        self.assertEqual(audit_log[0]["official_id"], "official_beta")
        self.assertEqual(audit_log[0]["new_status"], "verified")

    def test_lock_disputed_action_and_audit_trail(self):
        """Verify lock_disputed transitions status to 'locked_disputed' and creates audit entry."""
        result = hv_service.lock_disputed(
            structure_id="STR-006",
            official_id="official_beta",
            notes="Encroachment confirmed beyond acceptable margin.",
        )
        self.assertEqual(result["properties"]["status"], "locked_disputed")
        self.assertEqual(result["properties"]["verification_method"], "human_official")
        self.assertEqual(result["properties"]["human_verification"]["new_status"], "locked_disputed")

        audit_log = hv_service._load_audit_log(config.HUMAN_AUDIT_LOG_PATH)
        self.assertEqual(len(audit_log), 1)
        self.assertEqual(audit_log[0]["action"], "lock_disputed")
        self.assertEqual(audit_log[0]["structure_id"], "STR-006")

    # -----------------------------------------------------------------------
    # 3. Stage 4 Eligibility Filtering (§9, §17)
    # -----------------------------------------------------------------------
    def test_stage4_eligibility_rules(self):
        """
        Verify that:
        - GeoAI verified structures are included.
        - Human-verified structures (STR-005) are included.
        - Locked disputed structures (STR-006) are strictly excluded.
        """
        # Action STR-005 (verify) and STR-006 (lock disputed)
        hv_service.mark_verified("STR-005", "official_beta", "Verified in field")
        hv_service.lock_disputed("STR-006", "official_beta", "Confirmed encroachment")

        eligible = stage4_runner.get_eligible_verified_structures()
        eligible_ids = [f["properties"]["structure_id"] for f in eligible]

        self.assertIn("STR-002", eligible_ids)  # GeoAI verified
        self.assertIn("STR-003", eligible_ids)  # GeoAI verified
        self.assertIn("STR-005", eligible_ids)  # Human verified
        self.assertNotIn("STR-006", eligible_ids)  # Locked disputed MUST BE EXCLUDED
        self.assertNotIn("STR-007", eligible_ids)  # Un-actioned disputed MUST BE EXCLUDED

    # -----------------------------------------------------------------------
    # 4. Multi-Department Conflict Resolution (§9, §10, §24)
    # -----------------------------------------------------------------------
    def test_smart_rule_conflict_resolution_on_par104(self):
        """
        Test conflict resolution on PAR-104 where departments deliberately conflict:
        - Owner: Registration='Owner_C_Registered', Revenue='Owner_C_Revenue', ULB='Owner_C'
        - Land use: UDA='commercial', ULB='mixed_use', Revenue='mixed_use'
        """
        resolver = SmartRuleConflictResolver()
        dept_records = {
            "revenue_department": {
                "owner_name": "Owner_C_Revenue",
                "purpose_of_use": "mixed_use",
                "land_area_sqm": "85400",
            },
            "urban_local_body": {
                "owner_name": "Owner_C",
                "purpose_of_use": "mixed_use",
                "land_area_sqm": "85400",
            },
            "urban_development_authority": {
                "owner_name": "Owner_C",
                "purpose_of_use": "commercial",
                "land_area_sqm": "85400",
            },
            "registration_stamps": {
                "owner_name": "Owner_C_Registered",
                "purpose_of_use": "mixed_use",
                "land_area_sqm": "85400",
            },
            "directorate_land_records": {
                "owner_name": "Owner_C",
                "purpose_of_use": "mixed_use",
                "land_area_sqm": "85400",
                "khasra_no": "KHS-104",
                "khata_no": "KHT-104",
            },
        }

        resolved = resolver.resolve_parcel(
            parcel_id="PAR-104",
            cadastral_feature=None,
            department_records=dept_records,
            verified_structures=[],
        )

        # Owner resolved to Registration statutory priority
        self.assertEqual(resolved["resolved_owner"], "Owner_C_Registered")
        self.assertTrue(resolved["conflict_summary"]["ownership"]["conflict_detected"])

        # Land-use resolved to UDA master plan statutory priority
        self.assertEqual(resolved["resolved_land_use"], "commercial")
        self.assertTrue(resolved["conflict_summary"]["land_use"]["conflict_detected"])

        # Provenance: source values must remain untouched
        self.assertEqual(
            resolved["source_provenance"]["revenue_department"]["owner_name"],
            "Owner_C_Revenue",
        )
        self.assertEqual(
            resolved["source_provenance"]["urban_development_authority"]["purpose_of_use"],
            "commercial",
        )

    # -----------------------------------------------------------------------
    # 5. Full Stage 4 Consolidation Runner (§10)
    # -----------------------------------------------------------------------
    def test_full_stage4_runner_execution(self):
        """Execute Stage 4 and verify generated Single Source of Truth artifacts."""
        # Mark STR-005 verified to test inclusion
        hv_service.mark_verified("STR-005", "official_beta", "Verified by Lekhpal")

        result = stage4_runner.run_stage4()
        self.assertEqual(result["status"], "success")
        self.assertGreater(result["total_parcels_consolidated"], 0)

        # Verify JSON output
        self.assertTrue(Path(config.STAGE4_CONSOLIDATED_JSON_PATH).exists())
        with open(config.STAGE4_CONSOLIDATED_JSON_PATH, "r", encoding="utf-8") as f:
            parcels = json.load(f)
        self.assertIsInstance(parcels, list)

        # Find PAR-105 which should now contain verified structure STR-005
        par_105 = next((p for p in parcels if p["parcel_id"] == "PAR-105"), None)
        self.assertIsNotNone(par_105)
        structure_ids = [s["structure_id"] for s in par_105["verified_structures"]]
        self.assertIn("STR-005", structure_ids)

        # Verify GeoJSON output
        self.assertTrue(Path(config.STAGE4_CONSOLIDATED_GEOJSON_PATH).exists())
        with open(config.STAGE4_CONSOLIDATED_GEOJSON_PATH, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        self.assertEqual(geojson_data["type"], "FeatureCollection")
        self.assertEqual(len(geojson_data["features"]), len(parcels))

    # -----------------------------------------------------------------------
    # 6. REST API Endpoints (§13)
    # -----------------------------------------------------------------------
    def test_api_auth_and_verification_flow(self):
        """Test authentication, queue retrieval, and human action via REST endpoints."""
        # 1. Login
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "official_beta", "password": "password123"},
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertEqual(login_resp.json()["user"]["tehsil"], "Tehsil-Beta")

        # 2. Queue retrieval
        queue_resp = self.client.get("/api/human-verification/queue?official_id=official_beta")
        self.assertEqual(queue_resp.status_code, 200)
        queue_data = queue_resp.json()
        self.assertEqual(queue_data["tehsil"], "Tehsil-Beta")

        # 3. Perform action
        action_resp = self.client.post(
            "/api/human-verification/action",
            json={
                "structure_id": "STR-005",
                "official_id": "official_beta",
                "action": "mark_verified",
                "notes": "API verification test",
            },
        )
        self.assertEqual(action_resp.status_code, 200)
        self.assertEqual(action_resp.json()["feature"]["properties"]["status"], "verified")

        # 4. Trigger Stage 4 consolidation
        s4_resp = self.client.post("/api/stage4/run")
        self.assertEqual(s4_resp.status_code, 200)

        # 5. Query consolidated parcel
        parcel_resp = self.client.get("/api/stage4/parcels/PAR-105")
        self.assertEqual(parcel_resp.status_code, 200)
        self.assertEqual(parcel_resp.json()["parcel"]["parcel_id"], "PAR-105")


if __name__ == "__main__":
    unittest.main()
