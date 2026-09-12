"""
Inference adapter interface and implementations.

Defines the contract that **every** inference backend must satisfy so
that downstream geospatial logic never changes when swapping the mock
for a real YOLOv11-seg model.

Current implementations
-----------------------
- **MockInferenceAdapter** — Deterministic synthetic detections.  Clearly
  labeled as NOT a trained AI model.
- **YOLOv11SegAdapter** — Stub that raises ``NotImplementedError`` until
  a trained model checkpoint is available.
"""

from __future__ import annotations

import hashlib
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.pipeline.stage1.tiling import TileInfo

logger = logging.getLogger(__name__)


# ── Detection data structure ─────────────────────────────────────────────

@dataclass
class Detection:
    """A single detected structure, in **pixel coordinates** of its tile.

    Attributes
    ----------
    pixel_polygon : list[tuple[float, float]]
        Ordered vertices ``(x_px, y_px)`` forming a closed polygon in the
        tile's pixel space.  The first and last vertex need *not* be the
        same — the consumer will close the ring.
    class_name : str
        Semantic class label, e.g. ``"building"``.
    confidence : float
        Model confidence in ``[0.0, 1.0]``.
    """
    pixel_polygon: list[tuple[float, float]]
    class_name: str
    confidence: float


# ── Abstract adapter ─────────────────────────────────────────────────────

class InferenceAdapter(ABC):
    """Interface that all inference backends must implement."""

    @abstractmethod
    def predict(self, tile: TileInfo) -> list[Detection]:
        """Run inference on a single tile.

        Parameters
        ----------
        tile : TileInfo
            Tile data and metadata (pixel array, transform, index, …).

        Returns
        -------
        list[Detection]
            Zero or more detections **in the tile's pixel coordinate space**.
        """

    @property
    @abstractmethod
    def provenance_tag(self) -> str:
        """Human-readable string identifying this adapter (for provenance)."""


# ── Mock adapter ─────────────────────────────────────────────────────────

class MockInferenceAdapter(InferenceAdapter):
    """**CLEARLY LABELED MOCK — NOT A TRAINED AI MODEL.**

    Produces deterministic synthetic "building" detections so the rest of
    the pipeline can be developed and tested without a real model.

    Determinism is achieved by seeding a per-tile RNG from
    ``(global_seed, tile_row, tile_col)``.  Re-running with the same seed
    yields identical output.

    Each tile gets 1–3 non-overlapping rectangular "buildings" placed
    inside a safe margin so they don't land right on the tile border
    (which would complicate dedup testing in uninteresting ways).
    """

    def __init__(self, seed: int = 42) -> None:
        self._seed = seed

    # -- public interface --------------------------------------------------

    def predict(self, tile: TileInfo) -> list[Detection]:
        rng = self._tile_rng(tile.tile_index)
        tile_h, tile_w = tile.pixel_data.shape[1], tile.pixel_data.shape[2]

        # Don't generate detections on tiny tiles (< 32 px in either dim)
        if tile_h < 32 or tile_w < 32:
            return []

        n_detections = rng.randint(1, 3)
        margin = 8                          # px from tile edge
        min_side, max_side = 20, 60         # building side range in px

        detections: list[Detection] = []
        occupied: list[tuple[float, float, float, float]] = []

        for _ in range(n_detections):
            for _attempt in range(20):       # retry to avoid overlaps
                w = rng.randint(min_side, min(max_side, tile_w - 2 * margin))
                h = rng.randint(min_side, min(max_side, tile_h - 2 * margin))
                x0 = rng.randint(margin, tile_w - w - margin)
                y0 = rng.randint(margin, tile_h - h - margin)
                x1, y1 = x0 + w, y0 + h

                # Simple overlap check against already-placed boxes
                if any(self._boxes_overlap(x0, y0, x1, y1, *occ)
                       for occ in occupied):
                    continue

                occupied.append((x0, y0, x1, y1))
                conf = round(rng.uniform(0.70, 0.99), 2)
                detections.append(Detection(
                    pixel_polygon=[
                        (float(x0), float(y0)),
                        (float(x1), float(y0)),
                        (float(x1), float(y1)),
                        (float(x0), float(y1)),
                    ],
                    class_name="building",
                    confidence=conf,
                ))
                break  # placed successfully

        logger.debug(
            "Mock: tile (%d,%d) → %d detection(s)",
            *tile.tile_index, len(detections),
        )
        return detections

    @property
    def provenance_tag(self) -> str:
        return f"mock_inference_adapter_v0.1 (seed={self._seed})"

    # -- internals ---------------------------------------------------------

    def _tile_rng(self, tile_index: tuple[int, int]) -> random.Random:
        """Per-tile deterministic RNG derived from the global seed."""
        h = hashlib.sha256(
            f"{self._seed}:{tile_index[0]}:{tile_index[1]}".encode()
        ).hexdigest()
        return random.Random(int(h, 16))

    @staticmethod
    def _boxes_overlap(
        ax0: float, ay0: float, ax1: float, ay1: float,
        bx0: float, by0: float, bx1: float, by1: float,
    ) -> bool:
        return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


# ── Real YOLOv11-seg adapter (stub) ─────────────────────────────────────

class YOLOv11SegAdapter(InferenceAdapter):
    """Production adapter for **YOLOv11-seg** instance segmentation.

    This stub exists so the interface is importable from day one.
    Attempting to call ``predict()`` will raise ``NotImplementedError``
    until a trained model checkpoint is loaded.
    """

    def __init__(self, model_path: str | None = None) -> None:
        self._model_path = model_path
        # When ready:
        #   from ultralytics import YOLO
        #   self._model = YOLO(model_path)

    def predict(self, tile: TileInfo) -> list[Detection]:
        raise NotImplementedError(
            "YOLOv11SegAdapter is a stub.  Provide a trained model checkpoint "
            "and implement this method to replace the mock adapter."
        )

    @property
    def provenance_tag(self) -> str:
        return f"yolov11_seg (model={self._model_path})"
