"""Monocular calibration helpers for manual reference or pixel ratio."""

from __future__ import annotations

from typing import Any


def estimate_pixel_scale_from_reference(reference_height_m: float | None, reference_pixel_height: float | None) -> dict[str, Any]:
    if reference_height_m in (None, 0) or reference_pixel_height in (None, 0):
        return {
            "status": "CALIBRATION_NOT_READY",
            "pixel_scale_m_per_px": None,
            "calibration_method": "no_calibration",
            "reason": "reference height and pixel height are required.",
        }
    return {
        "status": "CALIBRATION_READY_PROVISIONAL",
        "pixel_scale_m_per_px": float(reference_height_m) / float(reference_pixel_height),
        "calibration_method": "manual_reference_pixel_ratio",
        "reason": "Pixel scale from explicit operator reference.",
    }
