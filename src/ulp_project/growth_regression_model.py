"""Proxy-data model selection for pohon_sono growth prior.

The Excel rows are PROXY_NOT_FIELD_OBSERVED. This module provides a small,
deterministic baseline model only; it is not a biological accuracy claim.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .growth_prior_loader import DEFAULT_POHON_SONO_XLSX, load_proxy_rows, map_growth_columns
from .paths import PROJECT_ROOT

GROWTH_FOLDER = PROJECT_ROOT / "data" / "growth_model" / "pohon_sono"
DERIVED_DIR = PROJECT_ROOT / "data" / "runtime" / "growth_prior"
MODEL_SELECTION_SEED = 74166
_MODEL_CACHE: dict[tuple[str, float], dict[str, Any]] = {}

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
    public = {key: value for key, value in model.items() if key not in {"coefficients", "model_object"}}
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
    if model["status"] == "GROWTH_LINEAR_REGRESSION_READY_PROXY_DATASET" and features:
        values = [_to_float(payload.get(name)) for name in features]
        means = model.get("feature_means", {})
        vector = [means.get(name, 0.0) if value is None else value for name, value in zip(features, values)]
        estimator = model.get("model_object")
        if estimator is not None and hasattr(estimator, "predict"):
            try:
                growth_cm_q = float(estimator.predict([vector])[0])
            except Exception:
                growth_cm_q = _linear_or_mean_prediction(model, vector)
        else:
            growth_cm_q = _linear_or_mean_prediction(model, vector)
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
        "growth_model_status": model.get("growth_model_status", "GROWTH_MODEL_PROXY_FALLBACK_READY"),
        "selected_model_name": model.get("selected_model_name", model.get("method")),
        "validation_mae": model.get("validation_mae"),
        "validation_rmse": model.get("validation_rmse"),
        "validation_r2": model.get("validation_r2"),
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
        return {
            "status": "GROWTH_PRIOR_DATASET_NOT_FOUND",
            "growth_model_status": "GROWTH_MODEL_NOT_READY_NO_DATA",
            "row_count": 0,
            "path": str(excel or ""),
        }
    cache_key = (str(excel), excel.stat().st_mtime)
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
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
        result = _fallback_average(rows, excel, target)
        _MODEL_CACHE[cache_key] = result
        return result
    fit = _fit_model_selection(matrix, y)
    result = {
        "status": "GROWTH_LINEAR_REGRESSION_READY_PROXY_DATASET",
        "growth_model_status": "GROWTH_MODEL_READY_PROXY_VALIDATED",
        "path": str(excel),
        "row_count": len(rows),
        "training_rows_used": len(matrix),
        "n_rows": len(matrix),
        "n_train": fit["n_train"],
        "n_val": fit["n_val"],
        "method": fit["method"],
        "selected_model_name": fit["selected_model_name"],
        "validation_mae": fit["validation_mae"],
        "validation_rmse": fit["validation_rmse"],
        "validation_r2": fit["validation_r2"],
        "features": feature_names,
        "feature_columns": feature_names,
        "target": target,
        "target_column": target,
        "intercept": fit["intercept"],
        "coefficients": fit["coefficients"],
        "model_object": fit.get("model_object"),
        "feature_means": {feature: sum(row[index] for row in matrix) / len(matrix) for index, feature in enumerate(feature_names)},
        "target_mean_cm_quarter": sum(y) / len(y),
        "source_status": "PROXY_NOT_FIELD_OBSERVED",
        "not_final_biological_accuracy": True,
    }
    _write_runtime_artifact(result)
    _MODEL_CACHE[cache_key] = result
    return result


def _fit_model_selection(matrix: list[list[float]], y: list[float]) -> dict[str, Any]:
    split = _train_validation_split(matrix, y)
    candidates = _sklearn_candidates()
    scored: list[dict[str, Any]] = []
    for name, estimator in candidates:
        try:
            estimator.fit(split["x_train"], split["y_train"])
            pred = [float(value) for value in estimator.predict(split["x_val"])]
            metrics = _metrics(split["y_val"], pred)
            scored.append(
                {
                    "method": name,
                    "selected_model_name": name,
                    "model_object": estimator,
                    **metrics,
                    "intercept": float(getattr(estimator, "intercept_", 0.0) or 0.0),
                    "coefficients": [float(value) for value in getattr(estimator, "coef_", [])] if hasattr(estimator, "coef_") else [],
                    "n_train": len(split["x_train"]),
                    "n_val": len(split["x_val"]),
                }
            )
        except Exception:
            continue
    if scored:
        return sorted(scored, key=lambda item: (float(item["validation_mae"]), item["selected_model_name"]))[0]
    fit = _fit_linear_regression_fallback(matrix, y)
    predictions = [_linear_or_mean_prediction(fit, row) for row in split["x_val"]]
    return {
        **fit,
        **_metrics(split["y_val"], predictions),
        "selected_model_name": fit["method"],
        "model_object": None,
        "n_train": len(split["x_train"]),
        "n_val": len(split["x_val"]),
    }


def _sklearn_candidates() -> list[tuple[str, Any]]:
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
        from sklearn.linear_model import LinearRegression, Ridge
    except Exception:
        return []
    return [
        ("sklearn.LinearRegression", LinearRegression()),
        ("sklearn.Ridge", Ridge(alpha=1.0, random_state=MODEL_SELECTION_SEED)),
        ("sklearn.RandomForestRegressor", RandomForestRegressor(n_estimators=60, max_depth=6, random_state=MODEL_SELECTION_SEED, n_jobs=1)),
        ("sklearn.HistGradientBoostingRegressor", HistGradientBoostingRegressor(max_iter=80, random_state=MODEL_SELECTION_SEED)),
    ]


def _train_validation_split(matrix: list[list[float]], y: list[float]) -> dict[str, Any]:
    n = len(matrix)
    indices = list(range(n))
    # Deterministic holdout derived from NIM seed without importing random state globally.
    indices.sort(key=lambda index: ((index + 1) * MODEL_SELECTION_SEED) % 9973)
    val_count = max(2, min(max(2, n // 5), n - 2))
    val_idx = set(indices[:val_count])
    x_train = [row for index, row in enumerate(matrix) if index not in val_idx]
    y_train = [target for index, target in enumerate(y) if index not in val_idx]
    x_val = [row for index, row in enumerate(matrix) if index in val_idx]
    y_val = [target for index, target in enumerate(y) if index in val_idx]
    return {"x_train": x_train, "y_train": y_train, "x_val": x_val, "y_val": y_val}


def _metrics(y_true: list[float], y_pred: list[float]) -> dict[str, float]:
    if not y_true:
        return {"validation_mae": 0.0, "validation_rmse": 0.0, "validation_r2": 0.0}
    errors = [float(pred) - float(target) for target, pred in zip(y_true, y_pred)]
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors))
    mean_y = sum(y_true) / len(y_true)
    ss_tot = sum((target - mean_y) ** 2 for target in y_true)
    ss_res = sum(error * error for error in errors)
    r2 = 0.0 if ss_tot == 0 else 1.0 - (ss_res / ss_tot)
    return {"validation_mae": round(mae, 6), "validation_rmse": round(rmse, 6), "validation_r2": round(r2, 6)}


def _fit_linear_regression_fallback(matrix: list[list[float]], y: list[float]) -> dict[str, Any]:
    try:
        from sklearn.linear_model import LinearRegression

        model = LinearRegression()
        model.fit(matrix, y)
        return {"method": "sklearn.LinearRegression", "intercept": float(model.intercept_), "coefficients": [float(value) for value in model.coef_], "model_object": model}
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
        return {"method": "average_fallback", "intercept": mean, "coefficients": [0.0 for _ in matrix[0]], "model_object": None}


def _linear_or_mean_prediction(model: dict[str, Any], vector: list[float]) -> float:
    intercept = float(model.get("intercept", model.get("target_mean_cm_quarter", 12.0)) or 0.0)
    coefficients = model.get("coefficients") or []
    if coefficients:
        return intercept + sum(float(coef) * float(value) for coef, value in zip(coefficients, vector))
    return float(model.get("target_mean_cm_quarter", intercept or 12.0))


def _fallback_average(rows: list[dict[str, Any]], excel: Path, target: str) -> dict[str, Any]:
    values = [_to_float(row.get(target)) for row in rows if target]
    values = [float(value) for value in values if value is not None]
    return {
        "status": "GROWTH_PRIOR_READY_PROXY_DATASET_NO_REGRESSION",
        "growth_model_status": "GROWTH_MODEL_PROXY_FALLBACK_READY",
        "path": str(excel),
        "row_count": len(rows),
        "training_rows_used": len(values),
        "method": "average_fallback",
        "selected_model_name": "deterministic_median_or_average_fallback",
        "validation_mae": None,
        "validation_rmse": None,
        "validation_r2": None,
        "n_rows": len(values),
        "n_train": len(values),
        "n_val": 0,
        "features": [],
        "feature_columns": [],
        "target": target,
        "target_column": target,
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
        "growth_model_status": model.get("growth_model_status", "GROWTH_MODEL_NOT_READY_NO_DATA"),
        "selected_model_name": model.get("selected_model_name", ""),
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
        public = {key: value for key, value in result.items() if key not in {"coefficients", "model_object"}}
        (DERIVED_DIR / "pohon_sono_growth_model_status.json").write_text(json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        return
