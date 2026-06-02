"""Height estimation helpers using explicit calibration only."""

from __future__ import annotations

from typing import Any


def estimate_height_from_pixels(pixel_height: float | None, pixel_scale_m_per_px: float | None) -> dict[str, Any]:
    if pixel_height is None or pixel_scale_m_per_px is None:
        return {
            "height_m": None,
            "height_method": "pixel_scale",
            "height_confidence": "LOW",
            "calibration_status": "CALIBRATION_NOT_READY",
            "calibration_notes": "Need field reference, camera metadata, or manual measurement.",
        }
    return {
        "height_m": round(float(pixel_height) * float(pixel_scale_m_per_px), 3),
        "height_method": "pixel_scale",
        "height_confidence": "MEDIUM",
        "calibration_status": "CALIBRATION_PARTIAL",
        "calibration_notes": "Provisional estimate from explicit pixel scale.",
    }
