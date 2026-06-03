"""Measurement quality labels for Progress 5.4 camera geometry."""

from __future__ import annotations

from typing import Any


def build_progress5_4_quality(measurement: dict[str, Any], *, latency_ms: int | float | None = None, gps_accuracy_m: float | None = None) -> dict[str, Any]:
    score = 100
    reasons = list(measurement.get("reason_codes") or [])
    if measurement.get("model_status") == "MODEL_NOT_READY":
        score -= 35
        reasons.append("MODEL_NOT_READY")
    if measurement.get("calibration_status") != "CALIBRATION_READY_FROM_REFERENCE_OBJECT":
        score -= 30
        reasons.append("CALIBRATION_NOT_READY")
    if measurement.get("clearance_m") is None:
        score -= 25
        reasons.append("INSUFFICIENT_DATA")
    if latency_ms is not None and float(latency_ms) > 3000:
        score -= 15
        reasons.append("HIGH_LATENCY")
    if gps_accuracy_m is not None and float(gps_accuracy_m) > 20:
        score -= 10
        reasons.append("LOW_ACCURACY")
    score = max(score, 0)
    if score >= 80:
        label = "HIGH"
    elif score >= 55:
        label = "MEDIUM"
    elif score >= 30:
        label = "LOW"
    else:
        label = "VERY_LOW"
    return {"measurement_quality_score": score, "measurement_quality_label": label, "reason_codes": _dedupe(reasons)}


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(str(item))
    return result
