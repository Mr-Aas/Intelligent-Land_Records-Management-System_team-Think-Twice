"""
Unit and integration tests for Master Orchestrator and GeoServer modules (§14, §15).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add project root directory to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.geoserver import setup as gs_setup
from orchestration.run_full_pipeline import run_full_pipeline


class TestOrchestrationAndGeoServer(unittest.TestCase):
    """Test suite for master pipeline orchestration and GeoServer setup helpers."""

    def test_geoserver_status_check(self):
        """Verify check_geoserver_status returns valid status tuple."""
        is_online, message, caps = gs_setup.check_geoserver_status()
        self.assertIsInstance(is_online, bool)
        self.assertIsInstance(message, str)

    def test_run_full_pipeline_execution(self):
        """Execute the complete end-to-end master orchestrator and verify stage summary metrics."""
        summary = run_full_pipeline()
        self.assertIsInstance(summary, dict)
        self.assertIn("stage0", summary)
        self.assertIn("stage1", summary)
        self.assertIn("stage2", summary)
        self.assertIn("stage3", summary)
        self.assertIn("postgis_sync", summary)
        self.assertIn("stage4", summary)
        self.assertIn("total_execution_time_sec", summary)

        self.assertGreater(summary["stage1"]["extracted_structures_count"], 0)
        self.assertGreaterEqual(summary["stage2"]["matched_count"], 0)
        self.assertGreaterEqual(summary["stage4"]["consolidated_parcels_count"], 0)


if __name__ == "__main__":
    unittest.main()
