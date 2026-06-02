"""Small geometry helpers for YOLO bbox measurements."""

from __future__ import annotations

from statistics import median
from typing import Any


BBox = list[float]


def bbox_height(bbox: BBox) -> float:
    return max(0.0, float(bbox[3]) - float(bbox[1]))


def bbox_width(bbox: BBox) -> float:
    return max(0.0, float(bbox[2]) - float(bbox[0]))


def bbox_center(bbox: BBox) -> tuple[float, float]:
    return ((float(bbox[0]) + float(bbox[2])) / 2.0, (float(bbox[1]) + float(bbox[3])) / 2.0)


def bbox_top_y(bbox: BBox) -> float:
    return float(bbox[1])


def bbox_bottom_y(bbox: BBox) -> float:
    return float(bbox[3])


def meter_per_pixel(reference_height_m: float | None, reference_pixel_height: float | None) -> dict[str, Any]:
    if reference_height_m is None:
        return {"status": "REFERENCE_HEIGHT_REQUIRED", "meter_per_pixel": None}
    if reference_pixel_height is None or reference_pixel_height <= 0:
        return {"status": "REFERENCE_PIXEL_HEIGHT_REQUIRED", "meter_per_pixel": None}
    return {"status": "METER_PER_PIXEL_READY", "meter_per_pixel": float(reference_height_m) / float(reference_pixel_height)}


def object_height_from_bbox(bbox: BBox, scale_m_per_px: float) -> float:
    return round(bbox_height(bbox) * scale_m_per_px, 3)


def height_above_reference_base(bbox_or_y: BBox | float, reference_base_y: float, scale_m_per_px: float) -> float:
    y = bbox_top_y(bbox_or_y) if isinstance(bbox_or_y, list) else float(bbox_or_y)
    return round((float(reference_base_y) - y) * scale_m_per_px, 3)


def median_value(values: list[float]) -> float | None:
    return median(values) if values else None
