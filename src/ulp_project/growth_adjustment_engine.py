"""Growth adjustment from real/manual inputs only."""

from __future__ import annotations

from typing import Any


def adjust_growth_rate(base_growth_rate_m_per_day: float | None, factors: dict[str, Any] | None = None) -> dict[str, Any]:
    if base_growth_rate_m_per_day is None or base_growth_rate_m_per_day <= 0:
        return {"status": "INSUFFICIENT_GROWTH_RATE", "adjusted_growth_rate_m_per_day": None, "missing_inputs": ["base_growth_rate_m_per_day"]}
    factors = factors or {}
    multiplier = 1.0
    used: dict[str, float] = {}
    for name in ["season_factor", "rainfall_factor", "soil_ph_factor", "moisture_factor", "temperature_factor", "species_factor"]:
        value = factors.get(name)
        if value not in (None, ""):
            used[name] = float(value)
            multiplier *= float(value)
    return {"status": "GROWTH_ADJUSTED" if used else "BASELINE_OR_MANUAL_ONLY", "adjusted_growth_rate_m_per_day": base_growth_rate_m_per_day * multiplier, "used_factors": used}
