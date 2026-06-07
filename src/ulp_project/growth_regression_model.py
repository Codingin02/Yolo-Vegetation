"""Proxy-data linear regression for pohon_sono growth prior.

The Excel rows are PROXY_NOT_FIELD_OBSERVED. This module provides a small,
deterministic baseline model only; it is not a biological accuracy claim.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .growth_prior_loader import DEFAULT_POHON_SONO_XLSX, load_proxy_rows, map_growth_columns
from .paths import PROJECT_ROOT

GROWTH_FOLDER = PROJECT_ROOT / "data" / "growth_model" / "pohon_sono"
DERIVED_DIR = PROJECT_ROOT / "data" / "runtime" / "growth_prior"

FEATURES = [
    "soil_ph_h2o_proxy",
    "soil_ph_kcl_proxy",
    "rainfall_mm_quarter_proxy",
    "mean_temp_c_quarter_proxy",
    "mean_humidity_pct_quarter_proxy",
    "solar_radiation_kwh_m2_day_proxy",
    "soil_soc_g_kg_proxy",
    "soil_nitrogen_g_kg_proxy",
    "soil_cec_cmol_kg_proxy",
    "sand_pct_proxy",
    "silt_pct_proxy",
    "clay_pct_proxy",
    "quarter",
    "year",
]
TARGETS = ["height_growth_cm_q_prior", "growth_m_per_year", "estimated_height_growth_m_per_year", "growth_multiplier"]


def find_growth_proxy_excel(folder: Path | None = None) -> Path | None:
    folder = folder or GROWTH_FOLDER
    candidates = sorted(folder.glob("*.xlsx"), key=lambda item: (("pohon_sono" in item.name.lower()), item.stat().st_mtime), reverse=True)
    return candidates[0] if candidates else (DEFAULT_POHON_SONO_XLSX if DEFAULT_POHON_SONO_XLSX.exists() else None)


def growth_regression_status(path: Path | None = None) -> dict[str, Any]:
    model = build_growth_regression(path)
    public = {key: value for key, value in model.items() if key != "coefficients"}
    return {
        **public,
        "source_status": "PROXY_NOT_FIELD_OBSERVED",
        "field_observation_status": "NOT_FIELD_MEASURED",
        "not_final_biological_accuracy": True,
    }


def predict_growth_regression(payload: dict[str, Any] | None = None, *, path: Path | None = None) -> dict[str, Any]:
    payload = dict(payload or {})
    model = build_growth_regression(path)
    if model["status"] == "GROWTH_PRIOR_DATASET_NOT_FOUND":
        return _base_prediction(model, "GROWTH_PRIOR_DATASET_NOT_FOUND")
    if model["status"] not in {"GROWTH_LINEAR_REGRESSION_READY_PROXY_DATASET", "GROWTH_PRIOR_READY_PROXY_DATASET_NO_REGRESSION"}:
        return _base_prediction(model, model["status"])
    features = model.get("features", [])
    if model["status"] == "GROWTH_LINEAR_REGRESSION_READY_PROXY_DATASET" and model.get("coefficients"):
        values = [_to_float(payload.get(name)) for name in features]
        means = model.get("feature_means", {})
        vector = [means.get(name, 0.0) if value is None else value for name, value in zip(features, values)]
        intercept = float(model.get("intercept", 0.0))
        growth_cm_q = intercept + sum(float(coef) * float(value) for coef, value in zip(model["coefficients"], vector))
    else:
        growth_cm_q = float(model.get("target_mean_cm_quarter", 12.0))
    growth_year = max(0.15, min(2.4, (growth_cm_q * 4.0) / 100.0))
    clearance = _to_float(payload.get("clearance_m"))
    eta_3m = _eta_days(clearance, threshold=3.0, growth_m_per_year=growth_year)
    eta_4m = _eta_days(clearance, threshold=4.0, growth_m_per_year=growth_year)
    return {
        "status": "GROWTH_REGRESSION_PREDICTION_READY_PROXY_DATASET",
        "growth_prior_status": model["status"],
        "estimated_height_growth_m_per_year": round(growth_year, 3),
        "estimated_height_growth_m_per_month": round(growth_year / 12.0, 4),
        "estimated_clearance_reduction_m_per_month": round(growth_year / 12.0, 4),
        "eta_to_3m_clearance_days": eta_3m,
        "eta_3m_status": "INSUFFICIENT_GEOMETRY_DATA" if clearance is None else "ETA_3M_PROXY_PRIOR_READY",
        "eta_to_4m_monitoring_days": eta_4m,
        "source_status": "PROXY_NOT_FIELD_OBSERVED",
        "field_observation_status": "NOT_FIELD_MEASURED",
        "not_final_biological_accuracy": True,
        "not_final_biological_accuracy_claim": True,
        "model_method": model.get("method"),
        "dataset_row_count": model.get("row_count", 0),
        "limitations": [
            "PROXY_NOT_FIELD_OBSERVED",
            "Regresi linear ini baseline prior, bukan klaim akurasi biologis final.",
            "ETA 3m aktif hanya jika clearance_m valid dari geometry/calibration.",
        ],
    }


def build_growth_regression(path: Path | None = None) -> dict[str, Any]:
    excel = path or find_growth_proxy_excel()
    if excel is None or not excel.exists():
        return {"status": "GROWTH_PRIOR_DATASET_NOT_FOUND", "row_count": 0, "path": str(excel or "")}
    try:
        rows = load_proxy_rows(excel)
    except Exception as exc:
        return {"status": "GROWTH_PRIOR_DATASET_INVALID", "path": str(excel), "error_type": type(exc).__name__, "message": str(exc)[:300], "row_count": 0}
    if not rows:
        return {"status": "GROWTH_PRIOR_DATASET_INVALID", "path": str(excel), "row_count": 0}
    headers = list(rows[0].keys())
    mapped = map_growth_columns(headers)
    target = _first_present(headers, TARGETS) or mapped.get("growth")
    feature_names = [name for name in FEATURES if name in headers]
    if "quarter" not in feature_names and mapped.get("quarter"):
        feature_names.append(mapped["quarter"])
    if "year" not in feature_names and mapped.get("year"):
        feature_names.append(mapped["year"])
    if not target or not feature_names:
        return _fallback_average(rows, excel, target or "")
    matrix: list[list[float]] = []
    y: list[float] = []
    for row in rows:
        target_value = _to_float(row.get(target))
        values = [_to_float(row.get(feature)) for feature in feature_names]
        if target_value is None or any(value is None for value in values):
            continue
        matrix.append([float(value) for value in values])
        y.append(float(target_value))
    if len(matrix) < max(8, len(feature_names) + 1):
        return _fallback_average(rows, excel, target)
    fit = _fit_linear_regression(matrix, y)
    result = {
        "status": "GROWTH_LINEAR_REGRESSION_READY_PROXY_DATASET",
        "path": str(excel),
        "row_count": len(rows),
        "training_rows_used": len(matrix),
        "method": fit["method"],
        "features": feature_names,
        "target": target,
        "intercept": fit["intercept"],
        "coefficients": fit["coefficients"],
        "feature_means": {feature: sum(row[index] for row in matrix) / len(matrix) for index, feature in enumerate(feature_names)},
        "target_mean_cm_quarter": sum(y) / len(y),
        "source_status": "PROXY_NOT_FIELD_OBSERVED",
        "not_final_biological_accuracy": True,
    }
    _write_runtime_artifact(result)
    return result


def _fit_linear_regression(matrix: list[list[float]], y: list[float]) -> dict[str, Any]:
    try:
        from sklearn.linear_model import LinearRegression

        model = LinearRegression()
        model.fit(matrix, y)
        return {"method": "sklearn.LinearRegression", "intercept": float(model.intercept_), "coefficients": [float(value) for value in model.coef_]}
    except Exception:
        pass
    try:
        import numpy as np

        x = np.asarray([[1.0, *row] for row in matrix], dtype=float)
        target = np.asarray(y, dtype=float)
        coef, *_ = np.linalg.lstsq(x, target, rcond=None)
        return {"method": "numpy.linalg.lstsq", "intercept": float(coef[0]), "coefficients": [float(value) for value in coef[1:]]}
    except Exception:
        mean = sum(y) / len(y)
        return {"method": "average_fallback", "intercept": mean, "coefficients": [0.0 for _ in matrix[0]]}


def _fallback_average(rows: list[dict[str, Any]], excel: Path, target: str) -> dict[str, Any]:
    values = [_to_float(row.get(target)) for row in rows if target]
    values = [float(value) for value in values if value is not None]
    return {
        "status": "GROWTH_PRIOR_READY_PROXY_DATASET_NO_REGRESSION",
        "path": str(excel),
        "row_count": len(rows),
        "training_rows_used": len(values),
        "method": "average_fallback",
        "features": [],
        "target": target,
        "target_mean_cm_quarter": (sum(values) / len(values)) if values else 12.0,
        "source_status": "PROXY_NOT_FIELD_OBSERVED",
        "not_final_biological_accuracy": True,
    }


def _base_prediction(model: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "status": status,
        "growth_prior_status": status,
        "source_status": "PROXY_NOT_FIELD_OBSERVED",
        "field_observation_status": "NOT_FIELD_MEASURED",
        "not_final_biological_accuracy": True,
        "eta_3m_status": "INSUFFICIENT_GEOMETRY_DATA",
        "dataset_row_count": model.get("row_count", 0),
    }


def _eta_days(clearance_m: float | None, *, threshold: float, growth_m_per_year: float) -> int | str:
    if clearance_m is None:
        return "INSUFFICIENT_GEOMETRY_DATA"
    if clearance_m <= threshold:
        return 0
    monthly = growth_m_per_year / 12.0
    if monthly <= 0:
        return "INSUFFICIENT_GROWTH_PRIOR"
    return int(round(((clearance_m - threshold) / monthly) * 30))


def _first_present(headers: list[str], candidates: list[str]) -> str:
    normalized = {_normalize(header): header for header in headers}
    for candidate in candidates:
        if _normalize(candidate) in normalized:
            return normalized[_normalize(candidate)]
    return ""


def _normalize(value: Any) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value or "")).strip("_")


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _write_runtime_artifact(result: dict[str, Any]) -> None:
    try:
        DERIVED_DIR.mkdir(parents=True, exist_ok=True)
        public = {key: value for key, value in result.items() if key != "coefficients"}
        (DERIVED_DIR / "pohon_sono_growth_regression_status.json").write_text(json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        return
