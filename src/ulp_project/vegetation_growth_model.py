"""Growth adjustment model without fabricated growth rates."""

from __future__ import annotations

from typing import Any

from .species_profile import get_species_profile


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_growth_multipliers(environment: dict[str, Any], allow_provisional: bool = False) -> dict[str, Any]:
    required = ["season_label", "rainfall_30d_mm", "soil_ph", "soil_moisture_proxy"]
    missing = [field for field in required if environment.get(field) in (None, "")]
    if missing and not allow_provisional:
        return {
            "status": "INSUFFICIENT_ENVIRONMENTAL_DATA",
            "multiplier": None,
            "missing_inputs": missing,
            "reason": "Environmental inputs are incomplete and provisional mode is disabled.",
        }
    multiplier = 1.0
    flags = []
    if missing:
        flags.append("PROVISIONAL_ENVIRONMENTAL_MULTIPLIERS_DEFAULTED")
    rainfall = _to_float(environment.get("rainfall_30d_mm"))
    if rainfall is not None:
        multiplier *= 1.1 if rainfall >= 150 else 0.95 if rainfall <= 50 else 1.0
    soil_ph = _to_float(environment.get("soil_ph"))
    if soil_ph is not None:
        multiplier *= 1.0 if 5.5 <= soil_ph <= 7.5 else 0.9
    return {"status": "GROWTH_MULTIPLIER_READY" if not missing else "PROVISIONAL_GROWTH_MULTIPLIER", "multiplier": multiplier, "missing_inputs": missing, "data_quality_flags": flags}


def adjusted_growth_rate(species_name: str, environment: dict[str, Any], allow_provisional: bool = False, base_growth_rate_override: float | None = None) -> dict[str, Any]:
    profile = get_species_profile(species_name)
    base = _to_float(base_growth_rate_override if base_growth_rate_override is not None else profile.get("base_growth_rate_m_per_day"))
    if base is None or base <= 0:
        return {
            "status": "GROWTH_RATE_NOT_READY",
            "growth_rate_base_m_per_day": None,
            "growth_rate_adjusted_m_per_day": None,
            "reason": "Species growth rate is null; provide local calibration or literature source.",
            "required_missing_inputs": ["base_growth_rate_m_per_day"],
            "confidence": profile.get("confidence_level", "LOW"),
        }
    multipliers = calculate_growth_multipliers(environment, allow_provisional=allow_provisional)
    if multipliers["multiplier"] is None:
        return {
            "status": multipliers["status"],
            "growth_rate_base_m_per_day": base,
            "growth_rate_adjusted_m_per_day": None,
            "reason": multipliers["reason"],
            "required_missing_inputs": multipliers["missing_inputs"],
            "confidence": "LOW",
        }
    return {
        "status": "ADJUSTED_GROWTH_RATE_READY" if multipliers["status"] == "GROWTH_MULTIPLIER_READY" else "PROVISIONAL_ADJUSTED_GROWTH_RATE",
        "growth_rate_base_m_per_day": base,
        "growth_rate_adjusted_m_per_day": round(base * float(multipliers["multiplier"]), 6),
        "reason": "Adjusted growth rate is provisional until local validation.",
        "required_missing_inputs": multipliers["missing_inputs"],
        "confidence": "MEDIUM" if not multipliers["missing_inputs"] else "LOW",
    }
