"""Growth-rate adjustment with explicit no-fake-environment handling."""

from __future__ import annotations

from typing import Any

from .field_inspection_record import FieldInspectionRecord


ENVIRONMENT_FIELDS = [
    "season",
    "rainfall_mm",
    "temperature_c",
    "relative_humidity_percent",
    "soil_moisture",
    "soil_ph",
    "solar_radiation",
    "evapotranspiration",
    "wind_speed",
]


def build_environment_factors(record: FieldInspectionRecord) -> dict[str, Any]:
    missing = [field for field in ENVIRONMENT_FIELDS if getattr(record, field) in (None, "")]
    if missing:
        return {
            "status": "ENVIRONMENT_PARTIAL",
            "missing_inputs": missing,
            "multiplier": 1.0,
            "reason": "No environmental value is fabricated; manual/base growth rate is used as-is.",
        }
    return {
        "status": "ENVIRONMENT_READY",
        "missing_inputs": [],
        "multiplier": 1.0,
        "reason": "Environmental fields are present. Phase 11 keeps multiplier conservative until field validation.",
    }


def choose_adjusted_growth_rate(record: FieldInspectionRecord, species_base_growth_rate: float | None = None) -> dict[str, Any]:
    base = record.growth_rate_m_per_day if record.growth_rate_m_per_day is not None else species_base_growth_rate
    if base is None or base <= 0:
        return {
            "status": "GROWTH_RATE_NOT_READY",
            "adjusted_growth_rate_m_per_day": None,
            "base_growth_rate_m_per_day": base,
            "environmental_data_status": "ENVIRONMENT_MANUAL_REQUIRED",
            "missing_inputs": ["growth_rate_m_per_day"],
            "reason": "Provide manual growth rate or a calibrated species profile.",
        }
    factors = build_environment_factors(record)
    adjusted = round(base * float(factors["multiplier"]), 6)
    return {
        "status": "ADJUSTED_GROWTH_RATE_READY" if factors["status"] == "ENVIRONMENT_READY" else "PROVISIONAL_MANUAL_GROWTH_RATE",
        "adjusted_growth_rate_m_per_day": adjusted,
        "base_growth_rate_m_per_day": base,
        "environmental_data_status": factors["status"],
        "missing_inputs": factors["missing_inputs"],
        "reason": factors["reason"],
    }
