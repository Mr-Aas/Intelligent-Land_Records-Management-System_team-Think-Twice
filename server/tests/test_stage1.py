"""
Unit and integration tests for Stage 1: GeoAI Raster Feature Extraction.

Validates the full Stage 1 pipeline according to CODING_AGENT_MASTER_PROMPT.md:
- GeoTIFF opens correctly.
- CRS is read correctly.
- Tiles are generated correctly (including smaller-than-tile rasters and multi-tile grids).
- Pixel coordinates convert accurately to spatial coordinates via affine transform.
- Output geometries are valid Shapely polygons.
- Duplicate detections from overlapping tile boundaries are deduplicated.
- GeoJSON output is strictly valid and contains all required metadata.
- Generated structure IDs are stable and deterministic across runs.
- Provenance tag explicitly labels the mock inference adapter.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from rasterio.crs import CRS
from shapely.geometry import Polygon, shape

from app.pipeline.stage1.extraction import (
    ExtractedStructure,
    convert_tile_detections,
    deduplicate_structures,
    pixel_to_spatial_polygon,
)
from app.pipeline.stage1.inference import Detection, MockInferenceAdapter, YOLOv11SegAdapter
from app.pipeline.stage1.runner import run_stage1
from app.pipeline.stage1.tiling import (
    RasterMeta,
    TileInfo,
    _compute_tile_windows,
    generate_tiles,
    read_raster_metadata,
)


class TestStage1(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.sample_geotiff = self.temp_dir / "test_raster.tif"

        width, height = 256, 256
        west, north = 710000.0, 3315000.0
        res = 0.5
        transform = Affine(res, 0.0, west, 0.0, -res, north)
        data = np.ones((3, height, width), dtype=np.uint8) * 128

        with rasterio.open(
            self.sample_geotiff,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=3,
            dtype="uint8",
            crs=CRS.from_epsg(32643),
            transform=transform,
        ) as dst:
            dst.write(data)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_geotiff_opens_and_reads_crs(self):
        meta = read_raster_metadata(str(self.sample_geotiff))
        self.assertEqual(meta.width, 256)
        self.assertEqual(meta.height, 256)
        self.assertEqual(meta.band_count, 3)
        self.assertIn("32643", meta.crs)
        self.assertEqual(meta.transform[0], 0.5)

    def test_tile_computation_small_raster(self):
        windows = _compute_tile_windows(raster_width=256, raster_height=256, tile_size=1024, overlap=64)
        self.assertEqual(len(windows), 1)
        row, col, win = windows[0]
        self.assertEqual(row, 0)
        self.assertEqual(col, 0)
        self.assertEqual(win.width, 256)
        self.assertEqual(win.height, 256)

    def test_tile_computation_multitile(self):
        windows = _compute_tile_windows(raster_width=200, raster_height=100, tile_size=100, overlap=20)
        self.assertEqual(len(windows), 3)

    def test_pixel_to_spatial_conversion(self):
        coords = [(10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)]
        transform = Affine(0.5, 0.0, 710000.0, 0.0, -0.5, 3315000.0)

        poly = pixel_to_spatial_polygon(coords, transform)
        self.assertTrue(poly.is_valid)
        self.assertFalse(poly.is_empty)

        minx, miny, maxx, maxy = poly.bounds
        self.assertEqual(minx, 710005.0)
        self.assertEqual(maxx, 710010.0)
        self.assertEqual(miny, 3314990.0)
        self.assertEqual(maxy, 3314995.0)

    def test_mock_inference_adapter_is_deterministic(self):
        adapter1 = MockInferenceAdapter(seed=123)
        adapter2 = MockInferenceAdapter(seed=123)

        dummy_meta = RasterMeta(
            path="dummy.tif", crs="EPSG:32643", transform=Affine.identity(),
            width=256, height=256, band_count=3, dtype="uint8"
        )
        dummy_tile = TileInfo(
            tile_index=(0, 0),
            window=rasterio.windows.Window(0, 0, 256, 256),
            transform=Affine.identity(),
            pixel_data=np.zeros((3, 256, 256), dtype=np.uint8),
            bounds=(0, 0, 256, 256),
            crs="EPSG:32643",
            raster_meta=dummy_meta,
        )

        dets1 = adapter1.predict(dummy_tile)
        dets2 = adapter2.predict(dummy_tile)

        self.assertEqual(len(dets1), len(dets2))
        self.assertGreater(len(dets1), 0)
        for d1, d2 in zip(dets1, dets2):
            self.assertEqual(d1.pixel_polygon, d2.pixel_polygon)
            self.assertEqual(d1.confidence, d2.confidence)
            self.assertEqual(d1.class_name, "building")

        self.assertIn("mock", adapter1.provenance_tag.lower())

    def test_yolo_adapter_predict(self):
        adapter = YOLOv11SegAdapter(model_path="yolo11n-seg.pt")
        self.assertIn("yolov11_seg", adapter.provenance_tag)
        dummy_meta = RasterMeta(
            path="dummy.tif", crs="EPSG:32643", transform=Affine.identity(),
            width=64, height=64, band_count=3, dtype="uint8"
        )
        dummy_tile = TileInfo(
            tile_index=(0, 0),
            window=rasterio.windows.Window(0, 0, 64, 64),
            transform=Affine.identity(),
            pixel_data=np.zeros((3, 64, 64), dtype=np.uint8),
            bounds=(0, 0, 64, 64),
            crs="EPSG:32643",
            raster_meta=dummy_meta,
        )
        dets = adapter.predict(dummy_tile)
        self.assertIsInstance(dets, list)


    def test_deduplication_removes_overlapping_duplicates(self):
        poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        poly2 = Polygon([(0.5, 0.5), (10.5, 0.5), (10.5, 10.5), (0.5, 10.5)])
        poly3 = Polygon([(50, 50), (60, 50), (60, 60), (50, 60)])

        s1 = ExtractedStructure("id1", poly1, "building", 0.90, "(0,0)", "geoai", "mock")
        s2 = ExtractedStructure("id2", poly2, "building", 0.85, "(0,1)", "geoai", "mock")
        s3 = ExtractedStructure("id3", poly3, "building", 0.95, "(0,1)", "geoai", "mock")

        deduped = deduplicate_structures([s1, s2, s3], iou_threshold=0.5)
        self.assertEqual(len(deduped), 2)
        retained_ids = {s.structure_id for s in deduped}
        self.assertIn("id1", retained_ids)
        self.assertIn("id3", retained_ids)

    def test_full_stage1_pipeline_execution(self):
        out_geojson = self.temp_dir / "ai_extracted.geojson"

        saved_path, structures = run_stage1(
            geotiff_path=str(self.sample_geotiff),
            output_path=str(out_geojson),
            tile_size=128,
            overlap=32,
            use_mock=True,
            mock_seed=42,
        )

        self.assertTrue(saved_path.exists())
        self.assertGreater(len(structures), 0)

        with open(saved_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["type"], "FeatureCollection")
        self.assertIn("crs", data)
        self.assertEqual(len(data["features"]), len(structures))

        first_feat = data["features"][0]
        self.assertEqual(first_feat["type"], "Feature")
        geom = shape(first_feat["geometry"])
        self.assertTrue(geom.is_valid)
        self.assertFalse(geom.is_empty)

        props = first_feat["properties"]
        self.assertIn("structure_id", props)
        self.assertEqual(props["class"], "building")
        self.assertIn("confidence", props)
        self.assertEqual(props["source"], "geoai")
        self.assertIn("mock_inference_adapter", props["provenance"])

        # ID determinism test
        out_geojson2 = self.temp_dir / "ai_extracted_2.geojson"
        _, structures2 = run_stage1(
            geotiff_path=str(self.sample_geotiff),
            output_path=str(out_geojson2),
            tile_size=128,
            overlap=32,
            use_mock=True,
            mock_seed=42,
        )

        ids1 = [s.structure_id for s in structures]
        ids2 = [s.structure_id for s in structures2]
        self.assertEqual(ids1, ids2)


if __name__ == "__main__":
    unittest.main()
