"""Deterministic pohon_sono growth prior model.

This is a proxy-data prior, not a biological accuracy claim.
"""

from __future__ import annotations

from typing import Any


def predict_pohon_sono_growth(inputs: dict[str, Any]) -> dict[str, Any]:
    species = str(inputs.get("species") or "pohon_sono")
    clearance_m = _to_float(inputs.get("clearance_m"))
    quarter_growth_cm = _to_float(inputs.get("height_growth_cm_q_prior"))
    base_growth = _to_float(inputs.get("base_growth_m_per_year")) or (quarter_growth_cm * 4 / 100 if quarter_growth_cm is not None else 1.2)
    ph = _to_float(_first(inputs, "soil_ph_actual", "ph_h2o", "soil_ph_h2o_proxy", "soil_ph_proxy", "ph"))
    rainfall_q = _to_float(_first(inputs, "rainfall_quarter_mm", "rainfall_mm_quarter_proxy", "rainfall", "rain_mm"))
    temp = _to_float(_first(inputs, "mean_temp_c", "mean_temp_c_quarter_proxy", "temperature", "temp_c"))
    humidity = _to_float(_first(inputs, "relative_humidity", "mean_humidity_pct_quarter_proxy", "humidity"))
    soc = _to_float(_first(inputs, "soc", "soil_soc_g_kg_proxy", "organic_carbon"))
    nitrogen = _to_float(_first(inputs, "nitrogen", "soil_nitrogen_g_kg_proxy", "n"))
    cec = _to_float(_first(inputs, "cec", "soil_cec_cmol_kg_proxy"))
    urban_stress = _to_float(inputs.get("urban_stress_factor"))
    season = _season_factor(inputs.get("quarter"))

    ph_factor = _triangular(ph, optimum_low=6.0, optimum_high=7.2, hard_low=4.8, hard_high=8.2, default=0.88)
    annual_rain = rainfall_q * 4 if rainfall_q is not None and rainfall_q < 900 else rainfall_q
    rainfall_factor = _triangular(annual_rain, optimum_low=900, optimum_high=2200, hard_low=500, hard_high=3200, default=0.9)
    temperature_factor = _triangular(temp, optimum_low=24, optimum_high=27, hard_low=18, hard_high=34, default=0.9)
    humidity_factor = _triangular(humidity, optimum_low=60, optimum_high=85, hard_low=35, hard_high=98, default=0.9)
    fertility_factor = _fertility_factor(soc=soc, nitrogen=nitrogen, cec=cec)
    stress_factor = _clamp(urban_stress if urban_stress is not None else 0.9, 0.45, 1.15)

    growth_year = base_growth * ph_factor * rainfall_factor * temperature_factor * humidity_factor * fertility_factor * stress_factor * season
    growth_year = round(_clamp(growth_year, 0.15, 2.4), 3)
    growth_month = round(growth_year / 12, 4)
    eta_3m = _eta_days(clearance_m, threshold=3.0, reduction_per_month=growth_month)
    eta_4m = _eta_days(clearance_m, threshold=4.0, reduction_per_month=growth_month)
    limitations = [
        "PROXY_NOT_FIELD_OBSERVED",
        "Bukan klaim akurasi biologis final.",
        "Kalibrasi dengan observasi lapangan diperlukan sebelum keputusan operasional final.",
    ]
    if clearance_m is None:
        limitations.append("ETA clearance membutuhkan geometry/clearance valid.")
    return {
        "status": "GROWTH_PRIOR_PREDICTION_READY",
        "growth_prior_status": "GROWTH_PRIOR_READY_PROXY_DATASET",
        "species": species,
        "estimated_height_growth_m_per_year": growth_year,
        "estimated_height_growth_m_per_month": growth_month,
        "estimated_clearance_reduction_m_per_month": growth_month,
        "eta_to_3m_clearance_days": eta_3m,
        "eta_to_4m_monitoring_days": eta_4m,
        "confidence_band_low": round(growth_year * 0.65, 3),
        "confidence_band_median": growth_year,
        "confidence_band_high": round(growth_year * 1.35, 3),
        "source_status": str(inputs.get("source_status") or "PROXY_NOT_FIELD_OBSERVED"),
        "factor_summary": {
            "ph_factor": round(ph_factor, 3),
            "rainfall_factor": round(rainfall_factor, 3),
            "temperature_factor": round(temperature_factor, 3),
            "humidity_factor": round(humidity_factor, 3),
            "soil_fertility_factor": round(fertility_factor, 3),
            "urban_stress_factor": round(stress_factor, 3),
            "season_factor": round(season, 3),
        },
        "literature_bounds_note": "Pterocarpus indicus cocok sekitar 24-27 C, curah hujan 900-2200 mm/tahun, tanah neutral/slightly acidic; gunakan sebagai prior, bukan final claim.",
        "limitations": limitations,
        "not_final_accuracy_claim": True,
    }


def _eta_days(clearance_m: float | None, *, threshold: float, reduction_per_month: float) -> int | str:
    if clearance_m is None:
        return "INSUFFICIENT_GEOMETRY_DATA"
    if clearance_m <= threshold:
        return 0
    if reduction_per_month <= 0:
        return "INSUFFICIENT_GROWTH_PRIOR"
    return int(round(((clearance_m - threshold) / reduction_per_month) * 30))


def _triangular(value: float | None, *, optimum_low: float, optimum_high: float, hard_low: float, hard_high: float, default: float) -> float:
    if value is None:
        return default
    if optimum_low <= value <= optimum_high:
        return 1.0
    if value < optimum_low:
        return _clamp((value - hard_low) / (optimum_low - hard_low), 0.35, 1.0)
    return _clamp((hard_high - value) / (hard_high - optimum_high), 0.35, 1.0)


def _fertility_factor(*, soc: float | None, nitrogen: float | None, cec: float | None) -> float:
    factors = []
    if soc is not None:
        factors.append(_clamp(soc / 2.0, 0.65, 1.15))
    if nitrogen is not None:
        factors.append(_clamp(nitrogen / 0.2, 0.7, 1.1))
    if cec is not None:
        factors.append(_clamp(cec / 18.0, 0.75, 1.1))
    return sum(factors) / len(factors) if factors else 0.9


def _season_factor(quarter: Any) -> float:
    text = str(quarter or "").strip().lower()
    if text in {"1", "q1", "i"}:
        return 1.05
    if text in {"2", "q2", "ii"}:
        return 1.0
    if text in {"3", "q3", "iii"}:
        return 0.88
    if text in {"4", "q4", "iv"}:
        return 0.97
    return 0.95


def _first(values: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if values.get(key) not in {None, ""}:
            return values.get(key)
    return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
