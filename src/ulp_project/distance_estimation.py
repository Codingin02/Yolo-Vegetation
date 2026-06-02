"""Distance and clearance estimation helpers."""

from __future__ import annotations

from typing import Any

from .calibration import estimate_pixel_scale, load_calibration_config


def estimate_object_distance_to_conductor(
    object_center_px: tuple[float, float] | None,
    conductor_center_px: tuple[float, float] | None,
    meters_per_pixel: float | None = None,
    calibration_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    calibration_config = calibration_config or load_calibration_config()
    scale = estimate_pixel_scale(meters_per_pixel=meters_per_pixel or calibration_config.get("pixel_scale", {}).get("meters_per_pixel"))
    if scale["status"] != "READY" or object_center_px is None or conductor_center_px is None:
        return {"status": "CALIBRATION_NOT_READY", "distance_m": None, "pixel_distance": None}
    dx = float(object_center_px[0]) - float(conductor_center_px[0])
    dy = float(object_center_px[1]) - float(conductor_center_px[1])
    pixel_distance = (dx * dx + dy * dy) ** 0.5
    return {
        "status": "READY",
        "distance_m": pixel_distance * float(scale["meters_per_pixel"]),
        "pixel_distance": pixel_distance,
    }


def classify_clearance_risk(distance_m: float | None, calibration_config: dict[str, Any] | None = None) -> dict[str, Any]:
    if distance_m is None:
        return {"status": "CALIBRATION_NOT_READY", "risk_level": "unknown", "distance_m": None}
    calibration_config = calibration_config or load_calibration_config()
    thresholds = calibration_config.get("clearance_thresholds_m", {})
    danger_below = float(thresholds.get("danger_below", 1.5))
    warning_below = float(thresholds.get("warning_below", 3.0))
    if distance_m < danger_below:
        level = "danger"
    elif distance_m < warning_below:
        level = "warning"
    else:
        level = "safe"
    return {"status": "READY", "risk_level": level, "distance_m": float(distance_m)}
