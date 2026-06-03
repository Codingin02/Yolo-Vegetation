"""Manual/provisional ETA calculation for Phase 9 rough realtime demo."""

from __future__ import annotations

from typing import Any

from .eta_uncertainty import calculate_eta_to_unsafe_zone

CLEARANCE_THRESHOLD_M = 3.0


def parse_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_manual_eta(clearance_m: Any, growth_rate_m_per_day: Any) -> dict[str, Any]:
    clearance = parse_float(clearance_m)
    growth = parse_float(growth_rate_m_per_day)
    if clearance is None:
        return _insufficient("clearance_m is required.", ["clearance_m"])
    if clearance <= CLEARANCE_THRESHOLD_M:
        return {
            "status": "ALREADY_WITHIN_UNSAFE_ZONE" if clearance > 0 else "CONTACT_OR_OVERLAP_RISK",
            "mode": "PROVISIONAL_MANUAL_DEMO",
            "eta_days": 0.0,
            "eta_months": 0.0,
            "risk_priority": "CRITICAL",
            "reason": "clearance_m is at or below the 3m prototype unsafe-zone threshold.",
            "required_missing_inputs": [],
            "clearance_m": clearance,
            "growth_rate_m_per_day": growth,
            "clearance_threshold_m": CLEARANCE_THRESHOLD_M,
        }
    if growth is None:
        return _insufficient("growth_rate_m_per_day is required.", ["growth_rate_m_per_day"], clearance, growth)
    if growth <= 0:
        return _insufficient("growth_rate_m_per_day must be greater than zero.", ["growth_rate_m_per_day"], clearance, growth)
    eta = calculate_eta_to_unsafe_zone(clearance, growth, CLEARANCE_THRESHOLD_M)
    eta_days = eta["eta_expected_days"]
    eta_months = eta["eta_expected_months"]
    if eta_days <= 30:
        priority = "CRITICAL"
    elif eta_days <= 90:
        priority = "HIGH"
    elif eta_days <= 180:
        priority = "MEDIUM"
    else:
        priority = "LOW"
    return {
        "status": "OK",
        "mode": "PROVISIONAL_MANUAL_DEMO",
        "eta_days": round(eta_days, 2),
        "eta_months": round(eta_months, 2),
        "risk_priority": priority,
        "reason": "Manual provisional ETA demo toward 3m unsafe-zone threshold.",
        "required_missing_inputs": [],
        "clearance_m": clearance,
        "growth_rate_m_per_day": growth,
        "clearance_threshold_m": CLEARANCE_THRESHOLD_M,
    }


def _insufficient(reason: str, missing: list[str], clearance: float | None = None, growth: float | None = None) -> dict[str, Any]:
    return {
        "status": "INSUFFICIENT_DATA",
        "mode": "IMAGE_CAPTURE_ONLY_MODEL_NOT_READY",
        "eta_days": None,
        "eta_months": None,
        "risk_priority": "INSUFFICIENT_DATA",
        "reason": reason,
        "required_missing_inputs": missing,
        "clearance_m": clearance,
        "growth_rate_m_per_day": growth,
    }
