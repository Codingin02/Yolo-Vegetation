"""Build Phase 7 environmental features without inventing source data."""

from __future__ import annotations

from typing import Any

PHASE7_ENV_FIELDS = [
    "rainfall_mm_7d",
    "rainfall_mm_30d",
    "rainfall_mm_90d",
    "temperature_c_mean_7d",
    "temperature_c_mean_30d",
    "humidity_mean_7d",
    "humidity_mean_30d",
    "wind_speed_mean_7d",
    "season_label",
    "soil_ph",
    "soil_moisture_proxy",
    "soil_texture",
    "data_source",
    "source_timestamp",
    "data_quality",
]


def classify_season_from_rainfall(features: dict[str, Any]) -> dict[str, str]:
    season_label = features.get("season_label")
    if season_label:
        return {"season_status": "BMKG_SEASON", "season_label": str(season_label)}
    rainfall_30 = _to_float(features.get("rainfall_mm_30d"))
    rainfall_90 = _to_float(features.get("rainfall_mm_90d"))
    if rainfall_30 is None and rainfall_90 is None:
        return {"season_status": "UNKNOWN_SEASON", "season_label": "unknown"}
    proxy = rainfall_30 if rainfall_30 is not None else rainfall_90 / 3.0
    if proxy >= 150:
        label = "rainy_proxy"
    elif proxy <= 50:
        label = "dry_proxy"
    else:
        label = "transition_proxy"
    return {"season_status": "RAINFALL_PROXY_SEASON", "season_label": label}


def build_phase7_environmental_features(raw: dict[str, Any]) -> dict[str, Any]:
    features = {field: raw.get(field) for field in PHASE7_ENV_FIELDS}
    season = classify_season_from_rainfall(features)
    features["season_label"] = season["season_label"]
    missing = [field for field, value in features.items() if value in (None, "")]
    status = "ENVIRONMENTAL_DATA_READY" if not missing else "ENVIRONMENTAL_DATA_PARTIAL"
    if len(missing) == len(PHASE7_ENV_FIELDS) - 1:
        status = "ENVIRONMENTAL_DATA_NOT_READY"
    return {
        "status": status,
        "features": features,
        "season_status": season["season_status"],
        "missing_features": missing,
        "data_quality": "LOW" if missing else "MEDIUM",
    }


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
