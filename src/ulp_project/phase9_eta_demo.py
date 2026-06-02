"""Manual/provisional ETA calculation for Phase 9 rough realtime demo."""

from __future__ import annotations

from typing import Any


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
    if clearance <= 0:
        return {
            "status": "CONTACT_OR_OVERLAP_RISK",
            "mode": "PROVISIONAL_MANUAL_DEMO",
            "eta_days": 0.0,
            "eta_months": 0.0,
            "risk_priority": "CRITICAL",
            "reason": "clearance_m <= 0 indicates contact or overlap risk.",
            "required_missing_inputs": [],
            "clearance_m": clearance,
            "growth_rate_m_per_day": growth,
        }
    if growth is None:
        return _insufficient("growth_rate_m_per_day is required.", ["growth_rate_m_per_day"], clearance, growth)
    if growth <= 0:
        return _insufficient("growth_rate_m_per_day must be greater than zero.", ["growth_rate_m_per_day"], clearance, growth)
    eta_days = clearance / growth
    eta_months = eta_days / 30.4375
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
        "reason": "Manual provisional ETA demo from clearance_m / growth_rate_m_per_day.",
        "required_missing_inputs": [],
        "clearance_m": clearance,
        "growth_rate_m_per_day": growth,
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
