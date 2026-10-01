from __future__ import annotations

from functools import lru_cache
import logging
import math
from statistics import median
from typing import Any

from .geometry import configured_thresholds
from .storage import as_float


_LOGGER = logging.getLogger(__name__)
_NUMERIC_BOUNDS = {
    "tree_height_m": (0, 150), "crown_width_m": (0, 150), "crown_area_m2": (0, 30000),
    "clearance_m": (0, 100), "current_clearance_m": (0, 100),
    "previous_height_m": (0, 150), "previous_crown_width_m": (0, 150),
    "previous_crown_area_m2": (0, 30000), "previous_clearance_m": (0, 100),
    "elapsed_days": (0.000001, 36525), "time_since_last_pruning_days": (0, 36525),
    "month": (1, 12), "temperature": (-20, 60), "humidity": (0, 100), "rainfall": (0, 20000),
}
_MESSAGES = {
    "not_applicable": "Prediksi tidak berlaku",
    "insufficient_data": "Data pengukuran belum cukup",
    "insufficient_input": "Input prediksi belum cukup",
    "uncalibrated_device": "Perangkat belum dikalibrasi",
    "capture_protocol_required": "Protokol pengambilan belum terpenuhi",
    "conductor_not_detected": "Konduktor tidak terdeteksi",
    "threshold_not_configured": "Ambang jaringan belum dikonfigurasi",
    "threshold_incompatible": "Jenis pengukuran tidak cocok dengan ambang jaringan",
    "geometry_unreliable": "Geometri belum cukup andal",
    "insufficient_growth_reference": "Referensi pertumbuhan tajuk belum cukup",
    "insufficient_growth_history": "Riwayat pertumbuhan belum cukup",
    "error": "Prediksi tidak tersedia",
}


def validate_prediction_features(values: dict[str, Any]) -> None:
    for name, (minimum, maximum) in _NUMERIC_BOUNDS.items():
        value = values.get(name)
        if value is None or value == "":
            continue
        number = as_float(value)
        if isinstance(value, bool) or number is None or not minimum <= number <= maximum:
            raise ValueError("invalid prediction input")
        if name == "month" and not number.is_integer():
            raise ValueError("invalid prediction month")


def predict_growth(
    *,
    species: str | None,
    growth_stage: str | None,
    clearance_m: float | None,
    features: dict[str, Any] | None = None,
    geometry_status: str | None = None,
    risk_status: str | None = None,
    geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return _predict_growth(
            species=species, growth_stage=growth_stage, clearance_m=clearance_m,
            features=features, geometry_status=geometry_status, geometry=geometry,
        )
    except Exception as exc:
        _LOGGER.warning("Prediction failed: %s", type(exc).__name__)
        return _result("error", species, growth_stage, error="prediction unavailable")


def _predict_growth(
    *,
    species: str | None,
    growth_stage: str | None,
    clearance_m: float | None,
    features: dict[str, Any] | None,
    geometry_status: str | None,
    geometry: dict[str, Any] | None,
) -> dict[str, Any]:
    stage = str(growth_stage or "").strip() or None
    if species != "angsana":
        return _result("not_applicable", species, stage)
    values = dict(features or {})
    validate_prediction_features(values)
    # Only server-produced geometry can authorize an operational status.
    measured = (geometry or {}).get("measurements") or {}
    state = (geometry or {}).get("measurement_status") or geometry_status or "insufficient_data"
    clearance = as_float(measured.get("clearance_unrounded_m"))
    if clearance is None:
        clearance = as_float(measured.get("clearance_m"))
    if state != "ok":
        return _result(state if state in _MESSAGES else "insufficient_data", species, stage)
    if (
        not geometry
        or measured.get("measurement_confidence") not in {"medium", "high"}
        or geometry.get("conductor_detection_index") is None
        or clearance is None or not 0 <= clearance <= 100
    ):
        return _result("geometry_unreliable", species, stage)

    thresholds = configured_thresholds(measured.get("clearance_measurement_type") or "nearest")
    if not thresholds.get("action_ready"):
        return _result(thresholds.get("status") or "threshold_not_configured", species, stage, threshold=thresholds)
    action = as_float(thresholds.get("action_threshold_m"))
    if action is None or action <= 0:
        return _result("threshold_not_configured", species, stage)
    context = {
        "threshold": thresholds,
        "clearance_m": round(clearance, 1),
        "measurement_confidence": measured.get("measurement_confidence"),
        "measurement_uncertainty": measured.get("measurement_uncertainty"),
        "clearance_measurement_type": measured.get("clearance_measurement_type"),
    }
    if clearance <= action:
        return _result(
            "ok", species, stage, operational_status="TEBANG",
            estimated_days=0, days_to_action=0, days_to_prune=0, months_to_prune=0,
            display_status="TEBANG", **context,
        )
    if not stage or stage == "unknown":
        return _result("insufficient_input", species, stage, **context)

    values.update({**measured, "clearance_m": clearance, "tree_stage": stage})
    rate = _growth_rate(values, stage)
    if rate is None:
        return _result(
            "insufficient_growth_reference", species, stage,
            uncertainty="No compatible crown/clearance-rate evidence is available", **context,
        )
    if rate.get("target") == "crown_extension_rate_m_per_day" and values.get("crown_direction") != "toward_conductor":
        return _result("insufficient_growth_reference", species, stage, **context)
    estimated_rate = as_float(rate.get("rate_m_per_day"))
    if estimated_rate is None:
        return _result("insufficient_growth_reference", species, stage, **context)
    timing = time_to_threshold(
        clearance, action, estimated_rate,
        rate_low=as_float(rate.get("rate_low_m_per_day")),
        rate_high=as_float(rate.get("rate_high_m_per_day")),
    )
    if timing["status"] == "insufficient_growth_reference":
        return _result(
            "insufficient_growth_reference", species, stage,
            rate=rate, model=rate.get("model"),
            growth_rate_m_per_day=estimated_rate, growth_rate_source=rate.get("source"),
            prediction_confidence=rate.get("prediction_confidence") or "low",
            rate_direction="moving_away_or_geometry_changed", **context,
        )
    days = timing["estimated_days"]
    return _result(
        "ok", species, stage, operational_status="PANTAU",
        display_status=f"PANTAU | ~{days} HARI", prediction_window=f"~{days} hari",
        estimated_days=days, days_to_action=days, days_to_prune=days,
        months_to_prune=round(days / 30.4375, 1),
        range_days=timing["range_days"], rate=rate, model=rate.get("model"),
        prediction_low_days=timing["range_days"][0] if timing["range_days"] else None,
        prediction_high_days=timing["range_days"][1] if timing["range_days"] else None,
        growth_rate_m_per_day=estimated_rate, growth_rate_source=rate.get("source"),
        prediction_confidence=rate.get("prediction_confidence") or "low",
        predictor_mode=("trained_model" if rate.get("model") in {"HistGradientBoostingRegressor", "MLP"}
                        else "observed_rate" if str(rate.get("model") or "").startswith("observed_")
                        else "evidence_prior"),
        uncertainty_scope="rate evidence only; measurement uncertainty remains separate",
        **context,
    )


def time_to_threshold(
    clearance: float,
    action: float,
    rate: float,
    *,
    rate_low: float | None = None,
    rate_high: float | None = None,
) -> dict[str, Any]:
    if not all(math.isfinite(value) for value in (clearance, action, rate)) or clearance < 0 or action <= 0:
        raise ValueError("invalid time-to-threshold inputs")
    remaining = clearance - action
    if remaining <= 0:
        return {"status": "ok", "estimated_days": 0, "range_days": None}
    if rate <= 0:
        return {"status": "insufficient_growth_reference", "estimated_days": None, "range_days": None}

    def days_for(value: float) -> int:
        days = remaining / value
        if not math.isfinite(days):
            raise ValueError("non-finite prediction horizon")
        return max(1, round(days))

    interval = None
    if (
        rate_low is not None and rate_high is not None
        and math.isfinite(rate_low) and math.isfinite(rate_high)
        and rate_low <= rate <= rate_high and rate_high > 0
    ):
        interval = [days_for(rate_high), days_for(rate_low) if rate_low > 0 else None]
    return {"status": "ok", "estimated_days": days_for(rate), "range_days": interval}


def _growth_rate(features: dict[str, Any], stage: str) -> dict[str, Any] | None:
    from .predictor import observed_rate, predict_rate

    history = features.get("growth_history")
    if (
        isinstance(history, dict)
        and features.get("tree_id")
        and history.get("tree_id") == features["tree_id"]
        and features.get("conductor_id")
        and history.get("conductor_id") == features["conductor_id"]
        and history.get("tree_stage") == stage
    ):
        try:
            value = observed_rate(history)
            return {
                **value,
                "rate_low_m_per_day": None, "rate_high_m_per_day": None,
                "model": "observed_clearance_rate", "source": history.get("source_url"),
                "prediction_confidence": "medium",
                "uncertainty": "one observed interval; future rate uncertainty unavailable",
            }
        except ValueError:
            if str(features.get("crown_direction") or "") == "toward_conductor":
                try:
                    value = observed_rate(history, "crown_extension_rate_m_per_day")
                    return {
                        **value,
                        "rate_low_m_per_day": None, "rate_high_m_per_day": None,
                        "model": "observed_crown_extension_rate", "source": history.get("source_url"),
                        "prediction_confidence": "low",
                        "uncertainty": "directional crown interval used as clearance-rate proxy",
                    }
                except ValueError:
                    pass
    try:
        result = predict_rate(features)
        if result.get("status") == "ok":
            return result
    except Exception as exc:
        _LOGGER.warning("Rate predictor unavailable: %s", type(exc).__name__)
    return _evidence_prior(stage, str(features.get("crown_direction") or ""))


@lru_cache(maxsize=16)
def _evidence_prior(stage: str, crown_direction: str) -> dict[str, Any] | None:
    from .predictor import read_evidence

    supported = {"clearance_closure_rate_m_per_day"}
    if crown_direction == "toward_conductor":
        supported.add("crown_extension_rate_m_per_day")
    candidates = []
    for row in read_evidence():
        if (
            row.get("species") not in {"angsana", "Pterocarpus indicus"}
            or row.get("tree_stage") != stage
            or str(row.get("verified")).lower() != "true"
            or row.get("observation_type") not in {"individual_longitudinal", "aggregate_growth"}
            or row.get("metric_name") not in supported
            or row.get("metric_unit") != "m/day"
            or not row.get("source_id") or not row.get("source_url")
        ):
            continue
        rate = as_float(row.get("metric_value"))
        if rate is None:
            continue
        location, country = str(row.get("location") or "").lower(), str(row.get("country") or "").lower()
        priority = 0 if "surabaya" in location else 1 if country == "indonesia" else 2 if country in {
            "singapore", "malaysia", "thailand", "philippines", "vietnam", "brunei"
        } else 3
        evidence_rank = 0 if row["observation_type"] == "individual_longitudinal" else 1
        candidates.append((evidence_rank, priority, row, rate))
    if not candidates:
        return None
    best_rank = min((item[0], item[1]) for item in candidates)
    selected = [item for item in candidates if item[:2] == best_rank]
    direct = [item for item in selected if item[2]["metric_name"] == "clearance_closure_rate_m_per_day"]
    selected = direct or selected
    rates = [item[3] for item in selected]
    distinct_sources = {item[2]["source_id"] for item in selected}
    return {
        "target": selected[0][2]["metric_name"], "rate_m_per_day": median(rates),
        "rate_low_m_per_day": min(rates) if len(distinct_sources) >= 2 else None,
        "rate_high_m_per_day": max(rates) if len(distinct_sources) >= 2 else None,
        "model": "evidence_prior",
        "source": sorted({item[2]["source_url"] for item in selected}),
        "aggregate_items": len(selected),
        "prediction_confidence": "low",
        "uncertainty": "observed source range; not a calibrated confidence interval",
    }


def _result(status: str, species: str | None, stage: str | None, **values: Any) -> dict[str, Any]:
    return {
        "status": status, "prediction_status": status,
        "prediction_window": None, "display_status": _MESSAGES.get(status, "Data prediksi belum cukup"),
        "species": species, "growth_stage": stage,
        "operational_status": None, "risk_status": None,
        "estimated_days": None, "days_to_action": None, "days_to_prune": None,
        "months_to_prune": None, "range_days": None, "rate": None, "model": None,
        "prediction_low_days": None, "prediction_high_days": None,
        "growth_rate_m_per_day": None, "growth_rate_source": None, "prediction_confidence": None,
        "predictor_mode": "evidence_prior",
        "error": None, **values,
    }
