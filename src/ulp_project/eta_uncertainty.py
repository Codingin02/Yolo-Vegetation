"""ETA formula using distance until entering the 3m unsafe zone."""

from __future__ import annotations

from typing import Any


def calculate_eta_to_unsafe_zone(clearance_m: float | None, growth_rate_m_per_day: float | None, safe_clearance_min_m: float = 3.0) -> dict[str, Any]:
    if clearance_m is None:
        return {"eta_status": "INSUFFICIENT_CLEARANCE_DATA", "eta_min_days": None, "eta_expected_days": None, "eta_max_days": None}
    if clearance_m < safe_clearance_min_m:
        return {"eta_status": "ALREADY_WITHIN_UNSAFE_ZONE", "eta_min_days": 0, "eta_expected_days": 0, "eta_max_days": 0, "available_growth_distance_m": 0}
    if growth_rate_m_per_day is None or growth_rate_m_per_day <= 0:
        return {"eta_status": "INSUFFICIENT_GROWTH_RATE", "eta_min_days": None, "eta_expected_days": None, "eta_max_days": None}
    distance = max(clearance_m - safe_clearance_min_m, 0)
    expected = distance / growth_rate_m_per_day
    return {
        "eta_status": "ETA_TO_3M_THRESHOLD_READY",
        "eta_min_days": round(expected * 0.7, 2),
        "eta_expected_days": round(expected, 2),
        "eta_max_days": round(expected * 1.3, 2),
        "eta_expected_months": round(expected / 30.44, 2),
        "available_growth_distance_m": round(distance, 3),
        "uncertainty_reason": "Prototype uncertainty band +/-30% until local growth calibration exists.",
    }
