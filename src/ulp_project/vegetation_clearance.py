"""Clearance estimation between vegetation and electrical assets."""

from __future__ import annotations

from typing import Any

from .span_geometry import bbox_gap_pixels, infer_nearest_asset_type


def estimate_clearance_from_bboxes(
    vegetation_bbox: list[float] | None,
    asset_bbox: list[float] | None,
    pixel_scale_m_per_px: float | None,
    asset_type: str | None = None,
) -> dict[str, Any]:
    if vegetation_bbox is None or asset_bbox is None:
        return {
            "status": "CLEARANCE_NOT_READY",
            "clearance_m": None,
            "clearance_method": "bbox_gap",
            "clearance_confidence": "LOW",
            "calibration_status": "GEOMETRY_NOT_READY",
            "nearest_asset_type": infer_nearest_asset_type(asset_type),
            "missing_inputs": ["vegetation_bbox", "asset_bbox"],
        }
    gap_px = bbox_gap_pixels(vegetation_bbox, asset_bbox)
    if pixel_scale_m_per_px is None or gap_px is None:
        return {
            "status": "CLEARANCE_NOT_READY",
            "clearance_m": None,
            "clearance_method": "bbox_gap",
            "clearance_confidence": "LOW",
            "calibration_status": "CALIBRATION_NOT_READY",
            "nearest_asset_type": infer_nearest_asset_type(asset_type),
            "missing_inputs": ["pixel_scale_m_per_px"],
        }
    return {
        "status": "CLEARANCE_ESTIMATE_READY",
        "clearance_m": round(gap_px * pixel_scale_m_per_px, 3),
        "clearance_method": "bbox_gap_scaled",
        "clearance_confidence": "MEDIUM",
        "calibration_status": "CALIBRATION_PARTIAL",
        "nearest_asset_type": infer_nearest_asset_type(asset_type),
        "missing_inputs": [],
    }


def classify_operational_risk(clearance_m: float | None) -> str:
    if clearance_m is None:
        return "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA"
    if clearance_m < 0.5:
        return "KRITIS_SEGERA"
    if clearance_m < 1.5:
        return "PRIORITAS_TINGGI"
    if clearance_m < 3.0:
        return "JADWALKAN_PEMANGKASAN"
    if clearance_m < 5.0:
        return "PERLU_MONITORING"
    return "AMAN_MONITOR"
