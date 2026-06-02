"""Clearance estimation wrapper for Phase 7."""

from __future__ import annotations

from typing import Any

from .vegetation_clearance import estimate_clearance_from_bboxes


def estimate_clearance_to_asset(
    vegetation_bbox: list[float] | None,
    asset_bbox: list[float] | None,
    pixel_scale_m_per_px: float | None,
    asset_type: str | None,
) -> dict[str, Any]:
    result = estimate_clearance_from_bboxes(vegetation_bbox, asset_bbox, pixel_scale_m_per_px, asset_type)
    return {
        "clearance_m": result["clearance_m"],
        "clearance_method": result["clearance_method"],
        "clearance_confidence": result["clearance_confidence"],
        "calibration_status": result["calibration_status"],
        "calibration_notes": "OpenCV/YOLO refinement can improve this after trained model is ready.",
        "status": result["status"],
    }
