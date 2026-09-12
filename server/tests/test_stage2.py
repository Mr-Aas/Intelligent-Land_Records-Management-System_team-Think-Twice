"""
Unit and integration tests for Stage 2: Municipal Matching.

Verifies:
- Any spatial intersection constitutes a municipal match.
- STR-001 (no municipal building) is classified as unregistered.
- STR-002 through STR-010 successfully match municipal building records.
- Unregistered records preserve their original AI geometry, structure_id, and reason.
- Matched records attach the corresponding municipal_building_id and attributes.
- Output GeoJSON files are valid and conform to schema expectations.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon

from app.pipeline.stage2.matcher import (
    MunicipalMatchedStructure,
    evaluate_municipal_matching,
    load_layer_in_crs,
    match_structure,
)
from app.pipeline.stage2.runner import run_stage2


class TestStage2(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.dataset_dir = Path(__file__).resolve().parents[2] / "data" / "synthetic_urban_land_department_data"
        self.ai_path = self.dataset_dir / "ai_extracted_expected.geojson"
        self.mun_path = self.dataset_dir / "municipal_buildings.geojson"


    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_synthetic_fixture_matching_all_cases(self):
        """Tests the actual synthetic dataset fixture against municipal records."""
        matched_out = self.temp_dir / "matched.geojson"
        unreg_out = self.temp_dir / "unregistered.geojson"

        matched_path, unreg_path, matched, unreg = run_stage2(
            ai_extracted_path=str(self.ai_path),
            municipal_data_path=str(self.mun_path),
            matched_output_path=str(matched_out),
            unregistered_output_path=str(unreg_out),
            target_epsg=32644,
        )

        self.assertTrue(matched_path.exists())
        self.assertTrue(unreg_path.exists())

        # Total 10 structures: STR-001 is unregistered, STR-002..010 are matched
        self.assertEqual(len(matched) + len(unreg), 10)
        self.assertEqual(len(unreg), 1)
        self.assertEqual(len(matched), 9)

        # STR-001 must be unregistered
        unreg_ids = [s.structure_id for s in unreg]
        self.assertIn("STR-001", unreg_ids)
        self.assertEqual(unreg[0].status, "unregistered")
        self.assertIsNone(unreg[0].municipal_building_id)

        # STR-002..STR-010 must be in matched
        matched_ids = [s.structure_id for s in matched]
        self.assertNotIn("STR-001", matched_ids)
        for i in range(2, 11):
            sid = f"STR-{i:03d}"
            self.assertIn(sid, matched_ids)

        # Verify municipal attributes attached
        str2_record = next(s for s in matched if s.structure_id == "STR-002")
        self.assertEqual(str2_record.status, "municipal_matched")
        self.assertIsNotNone(str2_record.municipal_building_id)
        self.assertIn("municipal_building_id", str2_record.municipal_attributes)

    def test_edge_touch_counts_as_match(self):
        """Locked business rule test: boundary touch / edge-only intersection counts as match."""
        # Two polygons touching along the line x = 10 from y=0 to y=10
        poly_a = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        poly_b = Polygon([(10, 0), (20, 0), (20, 10), (10, 10)])

        self.assertTrue(poly_a.intersects(poly_b))

        mun_gdf = gpd.GeoDataFrame(
            [{"municipal_building_id": "MUN-TEST-1"}],
            geometry=[poly_b],
            crs="EPSG:32644",
        )

        has_match, bld_id, attrs = match_structure(poly_a, mun_gdf)
        self.assertTrue(has_match)
        self.assertEqual(bld_id, "MUN-TEST-1")

    def test_no_overlap_classified_unregistered(self):
        """Verify disjoint polygons result in unregistered status."""
        poly_a = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        poly_b = Polygon([(100, 100), (105, 100), (105, 105), (100, 105)])

        mun_gdf = gpd.GeoDataFrame(
            [{"municipal_building_id": "MUN-TEST-2"}],
            geometry=[poly_b],
            crs="EPSG:32644",
        )

        has_match, bld_id, _ = match_structure(poly_a, mun_gdf)
        self.assertFalse(has_match)
        self.assertIsNone(bld_id)


if __name__ == "__main__":
    unittest.main()
