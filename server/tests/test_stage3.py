"""
Unit and integration tests for Stage 3: Cadastral / Bhu-Naksha Validation.

Verifies:
- Primary parcel selection (largest intersection area) and deterministic tie-breaking.
- Related parcels tracking.
- Exceedance overflow distance computation.
- Fully contained structures -> verified.
- Small overflow (< threshold) -> verified (STR-004).
- Medium overflow (threshold <= overflow < 2*threshold) -> audit_pending (STR-005).
- Large overflow (>= 2*threshold) -> disputed (STR-006, STR-007).
- Full compliance with required data model (§7) and provenance tracking.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon

from app.pipeline.stage3.runner import run_stage3
from app.pipeline.stage3.validator import (
    CadastralValidatedRecord,
    compute_boundary_overflow_distance,
    determine_primary_and_related_parcels,
    evaluate_structure_cadastral,
)


class TestStage3(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.dataset_dir = Path(__file__).resolve().parents[2] / "data" / "synthetic_urban_land_department_data"
        self.outputs_dir = Path(__file__).resolve().parents[2] / "data" / "outputs"
        self.matched_path = self.outputs_dir / "stage2_municipal_matched.geojson"
        self.parcels_path = self.dataset_dir / "bhu_naksha_parcels.geojson"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_synthetic_fixture_cadastral_validation(self):
        """Tests all 9 municipally-matched structures against the cadastral dataset."""
        v_out = self.temp_dir / "verified.geojson"
        a_out = self.temp_dir / "audit_pending.geojson"
        d_out = self.temp_dir / "disputed.geojson"

        v_path, a_path, d_path, verified, audit_pending, disputed = run_stage3(
            matched_structures_path=str(self.matched_path),
            cadastral_parcels_path=str(self.parcels_path),
            verified_output_path=str(v_out),
            audit_pending_output_path=str(a_out),
            disputed_output_path=str(d_out),
            threshold=10.0,
            target_epsg=32644,
        )

        self.assertTrue(v_path.exists())
        self.assertTrue(a_path.exists())
        self.assertTrue(d_path.exists())

        # Total 9 matched structures evaluated
        total = len(verified) + len(audit_pending) + len(disputed)
        self.assertEqual(total, 9)

        v_ids = {r.structure_id for r in verified}
        a_ids = {r.structure_id for r in audit_pending}
        d_ids = {r.structure_id for r in disputed}

        # Expected based on dataset manifest:
        # STR-002, STR-003, STR-004, STR-008, STR-009, STR-010 -> verified
        self.assertEqual(v_ids, {"STR-002", "STR-003", "STR-004", "STR-008", "STR-009", "STR-010"})

        # STR-004 has 5m overflow (< 10m threshold)
        str4 = next(r for r in verified if r.structure_id == "STR-004")
        self.assertAlmostEqual(str4.overflow_measure, 5.0, places=1)
        self.assertEqual(str4.parcel_id, "PAR-104")
        self.assertIn("PAR-105", str4.related_parcel_ids)
        self.assertEqual(str4.verification_method, "geoai")

        # STR-005 has 15m overflow (10m <= 15m < 20m) -> audit_pending
        self.assertEqual(a_ids, {"STR-005"})
        str5 = audit_pending[0]
        self.assertAlmostEqual(str5.overflow_measure, 15.0, places=1)
        self.assertEqual(str5.status, "audit_pending")

        # STR-006 (30m overflow) and STR-007 (split across two parcels) -> disputed
        self.assertEqual(d_ids, {"STR-006", "STR-007"})
        str6 = next(r for r in disputed if r.structure_id == "STR-006")
        self.assertAlmostEqual(str6.overflow_measure, 30.0, places=1)
        self.assertEqual(str6.status, "disputed")

        str7 = next(r for r in disputed if r.structure_id == "STR-007")
        self.assertIn(str7.parcel_id, ("PAR-107", "PAR-108"))
        self.assertGreater(len(str7.related_parcel_ids), 0)

    def test_primary_parcel_tie_breaking(self):
        """Tests deterministic tie-breaking (alphabetically smaller parcel_id) when intersection areas are equal."""
        struct_poly = Polygon([(0, 0), (20, 0), (20, 10), (0, 10)])  # Area = 200
        # Parcel A: left half (0..10) -> area 100
        parcel_b = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        # Parcel B: right half (10..20) -> area 100
        parcel_a = Polygon([(10, 0), (20, 0), (20, 10), (10, 10)])

        gdf = gpd.GeoDataFrame(
            [
                {"parcel_id": "PAR-200", "geometry": parcel_b},
                {"parcel_id": "PAR-100", "geometry": parcel_a},
            ],
            crs="EPSG:32644",
        )

        primary, related = determine_primary_and_related_parcels(struct_poly, gdf)
        self.assertIsNotNone(primary)
        # PAR-100 should be selected over PAR-200 because 'PAR-100' < 'PAR-200'
        self.assertEqual(primary["parcel_id"], "PAR-100")
        self.assertEqual(related, ["PAR-200"])

    def test_contained_structure_zero_overflow(self):
        """Verify that structure completely inside parcel has overflow = 0.0."""
        struct_poly = Polygon([(2, 2), (8, 2), (8, 8), (2, 8)])
        parcel_poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])

        dist = compute_boundary_overflow_distance(struct_poly, parcel_poly)
        self.assertEqual(dist, 0.0)


if __name__ == "__main__":
    unittest.main()
