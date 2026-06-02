"""Deterministic vegetation growth risk skeleton."""

from __future__ import annotations

from datetime import date
from typing import Any

REQUIRED_GROWTH_FIELDS = [
    "point_id",
    "vegetation_class",
    "current_clearance_m",
    "estimated_growth_cm_per_month",
    "observation_date",
    "confidence_source",
]


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def predict_vegetation_growth_risk(input_dict: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_GROWTH_FIELDS if input_dict.get(field) in (None, "")]
    environmental_optional = [
        "rainfall_monthly_mm",
        "season_label",
        "soil_ph",
        "soil_type",
        "temperature_c",
        "humidity_percent",
        "pruning_history_date",
    ]
    missing_environmental = [field for field in environmental_optional if input_dict.get(field) in (None, "")]
    if missing:
        return {
            "status": "ENVIRONMENTAL_DATA_NOT_READY",
            "risk_level": "UNKNOWN",
            "predicted_months_to_threshold": None,
            "recommended_action_window": "DATA_REQUIRED",
            "missing_factors": missing + missing_environmental,
            "source_quality": input_dict.get("confidence_source") or "UNKNOWN",
            "explanation": "Required growth or clearance inputs are missing.",
        }

    clearance = _to_float(input_dict.get("current_clearance_m"))
    growth_cm = _to_float(input_dict.get("estimated_growth_cm_per_month"))
    if clearance is None or growth_cm is None or growth_cm <= 0:
        return {
            "status": "ENVIRONMENTAL_DATA_NOT_READY",
            "risk_level": "UNKNOWN",
            "predicted_months_to_threshold": None,
            "recommended_action_window": "DATA_REQUIRED",
            "missing_factors": ["numeric_clearance_or_growth"],
            "source_quality": input_dict.get("confidence_source") or "UNKNOWN",
            "explanation": "Clearance/growth values must be numeric and growth must be positive.",
        }

    threshold_m = 1.5
    warning_m = 3.0
    if clearance <= threshold_m:
        months = 0.0
        level = "CRITICAL"
        window = "IMMEDIATE_REVIEW"
    else:
        months = (clearance - threshold_m) / (growth_cm / 100.0)
        if clearance < warning_m:
            level = "WARNING"
            window = "SHORT_TERM_REVIEW"
        elif months <= 6:
            level = "WATCH"
            window = "SCHEDULE_REVIEW_WITHIN_6_MONTHS"
        else:
            level = "SAFE"
            window = "ROUTINE_MONITORING"

    status = "RULE_BASED_STUB" if not missing_environmental else "ENVIRONMENTAL_DATA_NOT_READY"
    return {
        "status": status,
        "risk_level": level,
        "predicted_months_to_threshold": round(months, 2),
        "recommended_action_window": window,
        "missing_factors": missing_environmental,
        "source_quality": input_dict.get("confidence_source") or "UNKNOWN",
        "explanation": "Rule-based planning estimate; not a final scientific prediction.",
    }
