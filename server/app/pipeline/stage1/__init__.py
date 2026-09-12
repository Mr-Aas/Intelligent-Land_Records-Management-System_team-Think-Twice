"""
stage1 — GeoAI Raster Feature Extraction.

Tiles a GeoTIFF, runs instance-segmentation inference (YOLOv11-seg or a
clearly-labeled mock), converts pixel detections to spatial coordinates,
deduplicates across overlapping tiles, and writes ``ai_extracted.geojson``.
"""
