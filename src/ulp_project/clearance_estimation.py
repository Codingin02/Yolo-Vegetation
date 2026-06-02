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


def estimate_phase8_clearance(
    crown_top_m: float | None = None,
    asset_height_m: float | None = None,
    span_mid_sag_height_m: float | None = None,
    horizontal_distance_to_asset_m: float | None = None,
    uncertainty_m: float | None = None,
    clearance_source: str = "unknown",
) -> dict[str, Any]:
    target_height = span_mid_sag_height_m if span_mid_sag_height_m is not None else asset_height_m
    if crown_top_m is None or target_height is None:
        return {
            "clearance_m": None,
            "minimum_clearance_m": None,
            "vertical_clearance_m": None,
            "horizontal_distance_m": horizontal_distance_to_asset_m,
            "uncertainty_m": uncertainty_m,
            "calibration_status": "CALIBRATION_NOT_READY",
            "calibration_method": clearance_source,
            "clearance_status": "INSUFFICIENT_DATA",
        }
    vertical_clearance = float(target_height) - float(crown_top_m)
    minimum_clearance = vertical_clearance - float(uncertainty_m or 0.0)
    return {
        "clearance_m": round(vertical_clearance, 3),
        "minimum_clearance_m": round(minimum_clearance, 3),
        "vertical_clearance_m": round(vertical_clearance, 3),
        "horizontal_distance_m": horizontal_distance_to_asset_m,
        "uncertainty_m": uncertainty_m or 0.0,
        "calibration_status": "CALIBRATION_PARTIAL" if clearance_source != "unknown" else "CALIBRATION_NOT_READY",
        "calibration_method": clearance_source,
        "clearance_status": "CLEARANCE_ESTIMATE_READY" if clearance_source != "unknown" else "INSUFFICIENT_DATA",
    }
