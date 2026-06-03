"""Final Progress 5.4 clearance zone policy."""

from __future__ import annotations

from typing import Any


def classify_progress5_4_zone(clearance_m: float | int | str | None) -> dict[str, Any]:
    clearance = _to_float(clearance_m)
    if clearance is None:
        return {
            "zone_status": "INSUFFICIENT_DATA",
            "risk_level": "INSUFFICIENT_DATA",
            "action_recommendation": "COMPLETE_CAMERA_CALIBRATION_AND_DETECTION",
        }
    if clearance <= 3.0:
        return {
            "zone_status": "TEBANG",
            "risk_level": "CRITICAL",
            "action_recommendation": "FIELD_REVIEW_FOR_PRUNING_OR_CUTTING_PRIORITY",
        }
    if clearance <= 4.0:
        return {
            "zone_status": "PANTAUAN",
            "risk_level": "MONITOR",
            "action_recommendation": "SCHEDULE_CLOSE_MONITORING_AND_VERIFY_CALIBRATION",
        }
    return {
        "zone_status": "AMAN",
        "risk_level": "LOW",
        "action_recommendation": "KEEP_HISTORICAL_MONITORING",
    }


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
