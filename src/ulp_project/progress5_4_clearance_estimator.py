"""Camera geometry clearance estimator for Progress 5.4."""

from __future__ import annotations

from typing import Any

from .progress5_4_geometry_config import load_geometry_config, pole_reference_height_m
from .progress5_4_object_keypoints import extract_object_keypoints
from .progress5_4_pixel_metric_scaling import calculate_pixel_metric_scale
from .progress5_4_zone_policy import classify_progress5_4_zone


def estimate_clearance_from_detections(
    detections: list[dict[str, Any]],
    *,
    geometry_config: dict[str, Any] | None = None,
    latency_ms: int | float | None = None,
) -> dict[str, Any]:
    cfg = geometry_config or load_geometry_config()
    keypoints = extract_object_keypoints(detections)
    reference_height = pole_reference_height_m(cfg)
    scale = calculate_pixel_metric_scale(keypoints.get("pole_pixel_height"), reference_height)
    reason_codes: list[str] = []
    if not keypoints["pole_detected"]:
        reason_codes.append("REFERENCE_OBJECT_NOT_FOUND")
    if not keypoints["conductor_detected"]:
        reason_codes.append("CONDUCTOR_NOT_DETECTED")
    if not keypoints["tree_detected"]:
        reason_codes.append("TREE_NOT_DETECTED")
    if latency_ms is not None and float(latency_ms) > 3000:
        reason_codes.append("HIGH_LATENCY")
    if scale["status"] != "PIXEL_METRIC_SCALE_READY":
        reason_codes.append(scale["status"])
        return _insufficient_result(keypoints, scale, cfg, reason_codes)
    if not keypoints["conductor_detected"] or not keypoints["tree_detected"]:
        return _insufficient_result(keypoints, scale, cfg, reason_codes)

    meter_per_px = float(scale["meter_per_px"])
    pole_base_y = float(keypoints["pole_base_px"])
    tree_top_y = float(keypoints["tree_top_px"])
    tree_bottom_y = float(keypoints.get("tree_bottom_px") or pole_base_y)
    cable_y = float(keypoints["cable_px"])
    tree_height_m = max(tree_bottom_y - tree_top_y, 0.0) * meter_per_px
    tree_top_height_m = max(pole_base_y - tree_top_y, 0.0) * meter_per_px
    cable_height_m = max(pole_base_y - cable_y, 0.0) * meter_per_px
    clearance_m = (tree_top_y - cable_y) * meter_per_px
    zone = classify_progress5_4_zone(clearance_m)
    if "GROUND_LINE_UNVERIFIED" not in reason_codes:
        reason_codes.append("GROUND_LINE_UNVERIFIED")
    confidence_status = "PROVISIONAL_GEOMETRY_READY" if not reason_codes or reason_codes == ["GROUND_LINE_UNVERIFIED"] else "PROVISIONAL_WITH_WARNINGS"
    return {
        "status": "CAMERA_GEOMETRY_MEASUREMENT_READY",
        **keypoints,
        **scale,
        "tree_height_m": round(tree_height_m, 3),
        "tree_top_height_m": round(tree_top_height_m, 3),
        "cable_height_m": round(cable_height_m, 3),
        "clearance_m": round(clearance_m, 3),
        "clearance_px": round(tree_top_y - cable_y, 3),
        "zone_status": zone["zone_status"],
        "risk_level": zone["risk_level"],
        "action_recommendation": zone["action_recommendation"],
        "calibration_status": "CALIBRATION_READY_FROM_REFERENCE_OBJECT",
        "confidence_status": confidence_status,
        "geometry_source_status": cfg.get("source_status", "FIELD_DEFAULT_NEEDS_PLN_CONFIRMATION"),
        "reason_codes": _dedupe(reason_codes),
        "not_accuracy_claim": True,
    }


def _insufficient_result(keypoints: dict[str, Any], scale: dict[str, Any], cfg: dict[str, Any], reason_codes: list[str]) -> dict[str, Any]:
    zone = classify_progress5_4_zone(None)
    return {
        "status": "CALIBRATION_NOT_READY" if scale["status"] != "PIXEL_METRIC_SCALE_READY" else "INSUFFICIENT_DETECTION_DATA",
        **keypoints,
        **scale,
        "tree_height_m": None,
        "cable_height_m": None,
        "clearance_m": None,
        "zone_status": zone["zone_status"],
        "risk_level": zone["risk_level"],
        "action_recommendation": zone["action_recommendation"],
        "calibration_status": "CALIBRATION_NOT_READY" if scale["status"] != "PIXEL_METRIC_SCALE_READY" else "DETECTION_INCOMPLETE",
        "confidence_status": "CALIBRATION_NOT_READY",
        "geometry_source_status": cfg.get("source_status", "FIELD_DEFAULT_NEEDS_PLN_CONFIRMATION"),
        "reason_codes": _dedupe(reason_codes or ["INSUFFICIENT_DATA"]),
        "not_accuracy_claim": True,
    }


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
