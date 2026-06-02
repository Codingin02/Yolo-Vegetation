"""Time-to-contact estimation without fake growth assumptions."""

from __future__ import annotations

from typing import Any


MULTIPLIER_FIELDS = [
    "season_multiplier",
    "rainfall_multiplier",
    "humidity_multiplier",
    "temperature_multiplier",
    "soil_ph_multiplier",
    "soil_moisture_multiplier",
    "pruning_history_multiplier",
    "local_calibration_multiplier",
]


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def adjusted_growth_rate_m_per_day(input_data: dict[str, Any]) -> dict[str, Any]:
    base = _to_float(input_data.get("species_base_growth_rate_m_per_day"))
    if base is None or base <= 0:
        return {"status": "GROWTH_RATE_NOT_READY", "growth_rate_m_per_day": None, "missing_inputs": ["species_base_growth_rate_m_per_day"]}
    missing = []
    multiplier = 1.0
    for field in MULTIPLIER_FIELDS:
        value = _to_float(input_data.get(field))
        if value is None:
            missing.append(field)
            continue
        multiplier *= value
    if missing:
        return {"status": "GROWTH_MULTIPLIERS_PARTIAL", "growth_rate_m_per_day": None, "missing_inputs": missing}
    return {"status": "GROWTH_RATE_READY", "growth_rate_m_per_day": base * multiplier, "missing_inputs": []}


def estimate_time_to_contact(clearance_m: float | None, input_data: dict[str, Any]) -> dict[str, Any]:
    if clearance_m is None:
        return {
            "status": "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA",
            "eta_days": None,
            "eta_months": None,
            "eta_days_min": None,
            "eta_days_mid": None,
            "eta_days_max": None,
            "confidence_level": "LOW",
            "data_quality_flags": ["CLEARANCE_NOT_READY"],
        }
    rate = adjusted_growth_rate_m_per_day(input_data)
    if rate["growth_rate_m_per_day"] is None:
        return {
            "status": "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA",
            "eta_days": None,
            "eta_months": None,
            "eta_days_min": None,
            "eta_days_mid": None,
            "eta_days_max": None,
            "confidence_level": "LOW",
            "data_quality_flags": rate["missing_inputs"],
        }
    mid_rate = float(rate["growth_rate_m_per_day"])
    eta_days_mid = clearance_m / mid_rate if mid_rate > 0 else None
    return {
        "status": "PROVISIONAL_ESTIMATE",
        "eta_days": round(eta_days_mid, 2) if eta_days_mid is not None else None,
        "eta_months": round(eta_days_mid / 30.44, 2) if eta_days_mid is not None else None,
        "eta_days_min": round((clearance_m / (mid_rate * 1.25)), 2),
        "eta_days_mid": round(eta_days_mid, 2),
        "eta_days_max": round((clearance_m / (mid_rate * 0.75)), 2),
        "confidence_level": "MEDIUM",
        "data_quality_flags": ["PROVISIONAL_ESTIMATE_NOT_ACCURACY_CLAIM"],
    }
