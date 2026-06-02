"""Unified environmental feature engine with no fabricated values."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

MANUAL_TEMPLATE = PROJECT_ROOT / "data" / "templates" / "environmental_manual_template.csv"
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "environmental"

REQUIRED_ENV_OUTPUTS = [
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


def build_environmental_features(
    *,
    point_id: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    observation_date: str | None = None,
    manual_csv: Path = MANUAL_TEMPLATE,
    overrides: dict[str, Any] | None = None,
    write_cache: bool = False,
) -> dict[str, Any]:
    overrides = overrides or {}
    manual = load_manual_environment_row(point_id, manual_csv)
    features = _empty_features(point_id, latitude, longitude, observation_date)
    if manual["status"] == "MANUAL_ENVIRONMENT_ROW_READY":
        features.update(manual["features"])
        features["source_status"] = "MANUAL_CSV_READY"
        features["environmental_source"] = str(manual_csv)
    for key, value in overrides.items():
        if key in features and value not in (None, ""):
            features[key] = value
            features["source_status"] = "OPERATOR_OVERRIDE_READY"
            features["environmental_source"] = "operator_payload"
    missing = [key for key in REQUIRED_ENV_OUTPUTS if features.get(key) in (None, "")]
    if missing:
        features["source_status"] = features.get("source_status") if features.get("source_status") != "SOURCE_NOT_AVAILABLE" else "SOURCE_NOT_AVAILABLE"
        features["freshness_status"] = "ENVIRONMENT_MANUAL_REQUIRED"
    else:
        features["freshness_status"] = "ENVIRONMENT_READY"
    result = {
        "status": "ENVIRONMENT_FEATURES_READY" if not missing else "ENVIRONMENT_FEATURES_PARTIAL",
        "features": features,
        "missing_inputs": missing,
        "adapters": {
            "bmkg_manual_or_api": source_not_available("BMKG fetch not executed in tests."),
            "open_meteo_optional": source_not_available("Open-Meteo optional; no internet fetch in tests."),
            "nasa_power_optional": source_not_available("NASA POWER optional; no internet fetch in tests."),
            "soilgrids_optional": source_not_available("SoilGrids optional; no internet fetch in tests."),
            "manual_csv": manual,
        },
        "not_fake_environment": True,
    }
    if write_cache:
        cache_environmental_result(result, point_id or "unknown")
    return result


def load_manual_environment_row(point_id: str, path: Path = MANUAL_TEMPLATE) -> dict[str, Any]:
    if not path.exists():
        return {"status": "SOURCE_NOT_AVAILABLE", "features": {}, "missing_file": str(path)}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if point_id and row.get("point_id") != point_id:
                continue
            if not any((row.get(key) or "").strip() for key in REQUIRED_ENV_OUTPUTS):
                continue
            return {"status": "MANUAL_ENVIRONMENT_ROW_READY", "features": normalize_environment_row(row), "source": str(path)}
    return {"status": "SOURCE_NOT_AVAILABLE", "features": {}, "reason": "No matching manual CSV row with environmental values."}


def normalize_environment_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "season": row.get("season") or row.get("season_label") or "",
        "rainfall_mm": _to_float(row.get("rainfall_mm") or row.get("rainfall_30d_mm") or row.get("rainfall_7d_mm")),
        "temperature_c": _to_float(row.get("temperature_c") or row.get("temperature_avg_c") or row.get("temperature_2m_c")),
        "relative_humidity_percent": _to_float(row.get("relative_humidity_percent") or row.get("humidity_avg_percent") or row.get("relative_humidity_2m_percent")),
        "soil_moisture": _to_float(row.get("soil_moisture") or row.get("soil_moisture_proxy")),
        "soil_ph": _to_float(row.get("soil_ph")),
        "solar_radiation": _to_float(row.get("solar_radiation")),
        "evapotranspiration": _to_float(row.get("evapotranspiration")),
        "wind_speed": _to_float(row.get("wind_speed") or row.get("wind_speed_avg") or row.get("wind_speed_10m_ms")),
        "environmental_source": row.get("source_note") or row.get("data_source") or "manual_csv",
    }


def source_not_available(reason: str) -> dict[str, str]:
    return {"status": "SOURCE_NOT_AVAILABLE", "reason": reason, "cache_status": "NOT_WRITTEN"}


def cache_environmental_result(result: dict[str, Any], point_id: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{point_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _empty_features(point_id: str, latitude: float | None, longitude: float | None, observation_date: str | None) -> dict[str, Any]:
    return {
        "point_id": point_id,
        "latitude": latitude,
        "longitude": longitude,
        "date": observation_date or datetime.now().date().isoformat(),
        "season": None,
        "rainfall_mm": None,
        "temperature_c": None,
        "relative_humidity_percent": None,
        "soil_moisture": None,
        "soil_ph": None,
        "solar_radiation": None,
        "evapotranspiration": None,
        "wind_speed": None,
        "source_status": "SOURCE_NOT_AVAILABLE",
        "freshness_status": "ENVIRONMENT_MANUAL_REQUIRED",
        "environmental_source": "",
    }


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
