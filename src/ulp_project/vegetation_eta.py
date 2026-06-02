"""Phase 8 vegetation ETA calculation."""

from __future__ import annotations

from typing import Any

from .vegetation_growth_model import adjusted_growth_rate


def _months(days: float | None) -> float | None:
    return round(days / 30.44, 2) if days is not None else None


def estimate_vegetation_eta(
    clearance_m: float | None,
    species_name: str,
    environment: dict[str, Any] | None = None,
    allow_provisional: bool = False,
    base_growth_rate_override: float | None = None,
) -> dict[str, Any]:
    if clearance_m is None:
        return {
            "eta_status": "INSUFFICIENT_DATA",
            "days_to_contact_p50": None,
            "months_to_contact_p50": None,
            "days_to_contact_p10": None,
            "days_to_contact_p90": None,
            "confidence": "LOW",
            "reason": "minimum_clearance_m is required.",
            "required_missing_inputs": ["minimum_clearance_m"],
        }
    if clearance_m <= 0:
        return {
            "eta_status": "DANGER_NOW",
            "days_to_contact_p50": 0,
            "months_to_contact_p50": 0,
            "days_to_contact_p10": 0,
            "days_to_contact_p90": 0,
            "confidence": "HIGH",
            "reason": "clearance_m <= 0 means vegetation is already at or beyond contact threshold.",
            "required_missing_inputs": [],
        }
    rate = adjusted_growth_rate(species_name, environment or {}, allow_provisional=allow_provisional, base_growth_rate_override=base_growth_rate_override)
    adjusted = rate["growth_rate_adjusted_m_per_day"]
    if adjusted is None:
        return {
            "eta_status": rate["status"],
            "days_to_contact_p50": None,
            "months_to_contact_p50": None,
            "days_to_contact_p10": None,
            "days_to_contact_p90": None,
            "confidence": rate["confidence"],
            "reason": rate["reason"],
            "required_missing_inputs": rate["required_missing_inputs"],
        }
    p50 = clearance_m / float(adjusted)
    return {
        "eta_status": "PROVISIONAL_ETA_READY" if allow_provisional else "ETA_READY",
        "days_to_contact_p50": round(p50, 2),
        "months_to_contact_p50": _months(p50),
        "days_to_contact_p10": round(p50 * 0.8, 2),
        "days_to_contact_p90": round(p50 * 1.25, 2),
        "confidence": rate["confidence"],
        "reason": "ETA is an estimate; final validation requires model, calibration, and ground truth.",
        "required_missing_inputs": rate["required_missing_inputs"],
        "growth_rate_base_m_per_day": rate["growth_rate_base_m_per_day"],
        "growth_rate_adjusted_m_per_day": adjusted,
    }
