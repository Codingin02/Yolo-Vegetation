"""Measurement quality scoring for field trial outputs."""

from __future__ import annotations

from typing import Any

from . import measurement_reason_codes as codes


def evaluate_measurement_quality(inputs: dict[str, Any]) -> dict[str, Any]:
    score = 100
    reason_codes: list[str] = []
    if inputs.get("model_status") == "MODEL_NOT_READY":
        score -= 30
        reason_codes.append(codes.MODEL_NOT_READY)
    if str(inputs.get("calibration_status", "")).startswith("CALIBRATION_NOT"):
        score -= 25
        reason_codes.append(codes.CALIBRATION_NOT_READY)
    if float(inputs.get("object_confidence") or 1.0) < 0.4:
        score -= 15
        reason_codes.append(codes.LOW_OBJECT_CONFIDENCE)
    if not inputs.get("tree_detected") or not inputs.get("asset_detected"):
        score -= 20
        reason_codes.append(codes.TREE_OR_CONDUCTOR_MISSING)
    if not inputs.get("structure_reference_ready", True):
        score -= 15
        reason_codes.append(codes.STRUCTURE_REFERENCE_MISSING)
    if float(inputs.get("latency_ms") or 0) > 3000:
        score -= 10
        reason_codes.append(codes.HIGH_LATENCY)
    if str(inputs.get("stability_status", "")).startswith("WAITING") or str(inputs.get("stability_status", "")) == "OUTLIER_REJECTED":
        score -= 10
        reason_codes.append(codes.UNSTABLE_CLEARANCE)
    if not inputs.get("gps_ready"):
        score -= 5
        reason_codes.append(codes.GPS_NOT_READY)
    if str(inputs.get("environmental_data_status", "")).endswith("PARTIAL") or inputs.get("environmental_data_status") in {"ENVIRONMENT_PARTIAL", "ENVIRONMENT_NOT_READY"}:
        score -= 5
        reason_codes.append(codes.ENVIRONMENT_PARTIAL)
    score = max(0, min(100, score))
    return {"measurement_quality_score": score, "measurement_quality_label": _label(score, inputs), "reason_codes": reason_codes or [codes.STABLE_RESULT]}


def _label(score: int, inputs: dict[str, Any]) -> str:
    if inputs.get("field_confirmed"):
        return "FIELD_CONFIRMED"
    if score >= 80:
        return "HIGH"
    if score >= 55:
        return "MEDIUM"
    if score >= 30:
        return "LOW"
    return "VERY_LOW"
