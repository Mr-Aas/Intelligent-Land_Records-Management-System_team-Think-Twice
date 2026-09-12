"""
extraction — Pixel-to-spatial coordinate conversion, deduplication, and GeoJSON export.

Takes raw pixel detections from tiles, transforms vertices into geospatial
coordinates using the tile-local affine transform, validates geometries with Shapely,
deduplicates detections occurring along overlapping tile seams, and outputs
valid GeoJSON features with stable structure IDs and provenance metadata.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from affine import Affine
from shapely.geometry import Polygon, mapping
from shapely.validation import make_valid

from app.pipeline.stage1.inference import Detection
from app.pipeline.stage1.tiling import TileInfo

logger = logging.getLogger(__name__)


@dataclass
class ExtractedStructure:
    """A detected structure converted to spatial coordinates."""
    structure_id: str
    geometry: Polygon
    class_name: str
    confidence: float
    source_tile: str
    source: str
    provenance: str

    def to_geojson_feature(self) -> dict:
        """Serializes the structure to a standard GeoJSON Feature."""
        return {
            "type": "Feature",
            "geometry": mapping(self.geometry),
            "properties": {
                "structure_id": self.structure_id,
                "class": self.class_name,
                "confidence": self.confidence,
                "source_tile": self.source_tile,
                "source": self.source,
                "provenance": self.provenance,
            },
        }


def pixel_to_spatial_polygon(
    pixel_coords: Sequence[tuple[float, float]],
    transform: Affine,
) -> Polygon:
    """Converts a sequence of (col, row) pixel coordinates to a Shapely Polygon

    using the provided affine transform.
    """
    # Modern Affine library uses @ operator for coordinate transformation
    spatial_coords = [transform @ (col, row) for col, row in pixel_coords]
    poly = Polygon(spatial_coords)
    if not poly.is_valid:
        poly = make_valid(poly)
        # In case make_valid returns a MultiPolygon or GeometryCollection, take the largest polygon
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda g: g.area)
        elif poly.geom_type == "GeometryCollection":
            polys = [g for g in poly.geoms if g.geom_type == "Polygon"]
            if polys:
                poly = max(polys, key=lambda g: g.area)
            else:
                poly = poly.convex_hull
    return poly


def generate_structure_id(
    geotiff_path: str,
    tile_index: tuple[int, int],
    detection_idx: int,
    confidence: float,
) -> str:
    """Generates a deterministic UUID based on source inputs."""
    seed_str = f"{Path(geotiff_path).name}:{tile_index[0]}:{tile_index[1]}:{detection_idx}:{confidence:.4f}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed_str))


def convert_tile_detections(
    tile: TileInfo,
    detections: Sequence[Detection],
    provenance_tag: str,
) -> list[ExtractedStructure]:
    """Converts pixel detections of a single tile into ExtractedStructure instances."""
    structures: list[ExtractedStructure] = []
    tile_str = f"({tile.tile_index[0]}, {tile.tile_index[1]})"

    for idx, det in enumerate(detections):
        poly = pixel_to_spatial_polygon(det.pixel_polygon, tile.transform)
        if poly.is_empty or poly.area <= 0:
            continue

        sid = generate_structure_id(
            geotiff_path=tile.raster_meta.path,
            tile_index=tile.tile_index,
            detection_idx=idx,
            confidence=det.confidence,
        )

        structures.append(
            ExtractedStructure(
                structure_id=sid,
                geometry=poly,
                class_name=det.class_name,
                confidence=det.confidence,
                source_tile=tile_str,
                source="geoai",
                provenance=provenance_tag,
            )
        )

    return structures


def compute_iou(geom_a: Polygon, geom_b: Polygon) -> float:
    """Calculates Intersection over Union (IoU) between two Shapely polygons."""
    if not geom_a.intersects(geom_b):
        return 0.0
    inter_area = geom_a.intersection(geom_b).area
    union_area = geom_a.union(geom_b).area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def deduplicate_structures(
    structures: Sequence[ExtractedStructure],
    iou_threshold: float = 0.5,
) -> list[ExtractedStructure]:
    """Deduplicates overlapping structures from adjacent tile boundaries using IoU.

    If two structures have an IoU above iou_threshold, the one with higher confidence is kept.
    In case of equal confidence, the first one encountered is retained.
    """
    if not structures:
        return []

    # Sort descending by confidence
    sorted_structs = sorted(structures, key=lambda s: s.confidence, reverse=True)
    kept: list[ExtractedStructure] = []

    for candidate in sorted_structs:
        is_duplicate = False
        for existing in kept:
            if compute_iou(candidate.geometry, existing.geometry) >= iou_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(candidate)

    logger.info(
        "Deduplication: %d raw detections reduced to %d unique structures (IoU threshold=%.2f)",
        len(structures),
        len(kept),
        iou_threshold,
    )
    return kept


def export_to_geojson(
    structures: Sequence[ExtractedStructure],
    output_path: str | Path,
    crs: str = "EPSG:4326",
) -> Path:
    """Writes a collection of ExtractedStructure objects to a GeoJSON file."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    features = [s.to_geojson_feature() for s in structures]
    feature_collection = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": crs},
        },
        "features": features,
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f, indent=2)

    logger.info("Exported %d features to GeoJSON: %s", len(features), out)
    return out
