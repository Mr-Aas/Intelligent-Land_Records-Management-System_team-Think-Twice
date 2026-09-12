"""
Rasterio-based tiling engine for GeoTIFF rasters.

Opens a GeoTIFF, validates its CRS and transform, then yields tiles of
configurable size with configurable overlap.  Each tile carries its own
affine transform so downstream code can convert pixel coordinates to
spatial coordinates independently.

Handles rasters smaller than the tile size (produces a single tile).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Iterator

import numpy as np
import rasterio
from rasterio.windows import Window
from affine import Affine

logger = logging.getLogger(__name__)


# ── Data structures ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class RasterMeta:
    """Immutable snapshot of the source GeoTIFF's metadata."""
    path: str
    crs: str              # e.g. "EPSG:32643"
    transform: Affine     # full-raster affine
    width: int            # total raster width in pixels
    height: int           # total raster height in pixels
    band_count: int
    dtype: str


@dataclass
class TileInfo:
    """Everything needed to process one tile independently."""
    tile_index: tuple[int, int]       # (row, col) in the tile grid
    window: Window                    # rasterio window into the source
    transform: Affine                 # tile-local affine transform
    pixel_data: np.ndarray            # shape (bands, height, width)
    bounds: tuple[float, float, float, float]   # (left, bottom, right, top)
    crs: str
    raster_meta: RasterMeta = field(repr=False)


# ── Raster I/O ───────────────────────────────────────────────────────────

def read_raster_metadata(geotiff_path: str) -> RasterMeta:
    """Open a GeoTIFF and read its metadata without loading pixel data.

    Validates that:
    - the file has a defined CRS,
    - the file has a valid (non-identity) affine transform.

    Raises
    ------
    FileNotFoundError
        If *geotiff_path* does not exist.
    ValueError
        If CRS or transform is missing/invalid.
    """
    with rasterio.open(geotiff_path) as ds:
        if ds.crs is None:
            raise ValueError(
                f"GeoTIFF at {geotiff_path} has no CRS. "
                "A valid CRS is required for spatial coordinate conversion."
            )

        transform = ds.transform
        if transform is None or transform == Affine.identity():
            raise ValueError(
                f"GeoTIFF at {geotiff_path} has no valid affine transform. "
                "Spatial positioning requires a real transform."
            )

        meta = RasterMeta(
            path=geotiff_path,
            crs=str(ds.crs),
            transform=transform,
            width=ds.width,
            height=ds.height,
            band_count=ds.count,
            dtype=str(ds.dtypes[0]),
        )

    logger.info(
        "Raster metadata: %s × %s px, %d bands, CRS=%s",
        meta.width, meta.height, meta.band_count, meta.crs,
    )
    return meta


# ── Tile generation ──────────────────────────────────────────────────────

def _compute_tile_windows(
    raster_width: int,
    raster_height: int,
    tile_size: int,
    overlap: int,
) -> list[tuple[int, int, Window]]:
    """Return a list of ``(row, col, Window)`` covering the entire raster.

    Tiles at the right / bottom edge may be smaller than *tile_size*.
    Each window's col_off / row_off accounts for the overlap so that
    neighboring tiles share *overlap* pixels of context.
    """
    if tile_size <= 0:
        raise ValueError(f"tile_size must be positive, got {tile_size}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= tile_size:
        raise ValueError(
            f"overlap ({overlap}) must be smaller than tile_size ({tile_size})"
        )

    step = tile_size - overlap
    n_cols = max(1, math.ceil((raster_width - overlap) / step))
    n_rows = max(1, math.ceil((raster_height - overlap) / step))

    windows: list[tuple[int, int, Window]] = []
    for row_idx in range(n_rows):
        for col_idx in range(n_cols):
            col_off = col_idx * step
            row_off = row_idx * step

            # Clamp to raster bounds
            win_width = min(tile_size, raster_width - col_off)
            win_height = min(tile_size, raster_height - row_off)

            if win_width <= 0 or win_height <= 0:
                continue

            windows.append((
                row_idx,
                col_idx,
                Window(col_off=col_off, row_off=row_off,
                       width=win_width, height=win_height),
            ))

    logger.info(
        "Generated %d tiles (%d rows × %d cols) for %d×%d raster "
        "(tile=%d, overlap=%d)",
        len(windows), n_rows, n_cols,
        raster_width, raster_height, tile_size, overlap,
    )
    return windows


def generate_tiles(
    geotiff_path: str,
    tile_size: int,
    overlap: int,
) -> Iterator[TileInfo]:
    """Yield :class:`TileInfo` objects for every tile in the GeoTIFF.

    Parameters
    ----------
    geotiff_path : str
        Path to the source GeoTIFF.
    tile_size : int
        Tile width/height in pixels.
    overlap : int
        Number of overlapping pixels on each edge between adjacent tiles.

    Yields
    ------
    TileInfo
        One per tile, containing pixel data and spatial metadata.
    """
    meta = read_raster_metadata(geotiff_path)
    tile_windows = _compute_tile_windows(
        meta.width, meta.height, tile_size, overlap,
    )

    with rasterio.open(geotiff_path) as ds:
        for row_idx, col_idx, window in tile_windows:
            # Tile-local affine transform: maps this tile's pixel coords
            # to the same spatial CRS as the full raster.
            tile_transform = ds.window_transform(window)

            pixel_data = ds.read(window=window)  # shape (bands, h, w)

            # Spatial bounds of this tile
            bounds = rasterio.windows.bounds(window, ds.transform)

            yield TileInfo(
                tile_index=(row_idx, col_idx),
                window=window,
                transform=tile_transform,
                pixel_data=pixel_data,
                bounds=bounds,
                crs=str(ds.crs),
                raster_meta=meta,
            )
