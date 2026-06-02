"""Calibration readiness checks without fabricating calibration values."""

from __future__ import annotations

from typing import Any


CHECKS = [
    "camera_reference_object",
    "known_pole_or_cable_height",
    "pixel_to_meter_ratio",
    "gps_available",
    "yolo_model_available",
]


def check_calibration_readiness(inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    inputs = inputs or {}
    missing = [name for name in CHECKS if not inputs.get(name)]
    status = "CALIBRATION_READY_FOR_FIELD_TEST" if not missing else "CALIBRATION_WAITING_FOR_FIELD_DATA"
    return {
        "status": status,
        "missing_inputs": missing,
        "checks": {name: bool(inputs.get(name)) for name in CHECKS},
        "not_accuracy_claim": True,
    }
