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


def estimate_tree_asset_heights(
    tree_pixel_height: float | None,
    asset_pixel_height: float | None,
    pixel_scale_m_per_px: float | None,
) -> dict[str, Any]:
    tree = estimate_height_from_pixels(tree_pixel_height, pixel_scale_m_per_px)
    asset = estimate_height_from_pixels(asset_pixel_height, pixel_scale_m_per_px)
    return {
        "estimated_tree_height_m": tree["height_m"],
        "estimated_asset_height_m": asset["height_m"],
        "calibration_status": tree["calibration_status"] if tree["calibration_status"] == asset["calibration_status"] else "CALIBRATION_PARTIAL",
        "calibration_method": tree["height_method"],
        "height_confidence": tree["height_confidence"],
    }
