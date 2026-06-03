"""Pixel-to-meter scaling helpers for Progress 5.4 geometry."""

from __future__ import annotations

from typing import Any


def calculate_pixel_metric_scale(pole_pixel_height: float | int | str | None, pole_reference_height_m: float | int | str | None) -> dict[str, Any]:
    pole_px = _to_float(pole_pixel_height)
    pole_m = _to_float(pole_reference_height_m)
    if pole_m is None or pole_m <= 0:
        return {"status": "REFERENCE_HEIGHT_REQUIRED", "meter_per_px": None, "px_per_meter": None}
    if pole_px is None or pole_px <= 0:
        return {"status": "REFERENCE_OBJECT_NOT_FOUND", "meter_per_px": None, "px_per_meter": None, "pole_reference_height_m": pole_m}
    meter_per_px = pole_m / pole_px
    return {
        "status": "PIXEL_METRIC_SCALE_READY",
        "pole_pixel_height": round(pole_px, 3),
        "pole_reference_height_m": round(pole_m, 3),
        "meter_per_px": round(meter_per_px, 6),
        "px_per_meter": round(1.0 / meter_per_px, 3),
    }


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
