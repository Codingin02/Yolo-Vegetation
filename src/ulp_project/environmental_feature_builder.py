"""Build Phase 7 environmental features without inventing source data."""

from __future__ import annotations

from typing import Any

PHASE7_ENV_FIELDS = [
    "latitude",
    "longitude",
    "observation_date",
    "rainfall_mm_7d",
    "rainfall_mm_30d",
    "rainfall_mm_90d",
    "rainfall_7d_mm",
    "rainfall_30d_mm",
    "temperature_c_mean_7d",
    "temperature_c_mean_30d",
    "temperature_avg_c",
    "humidity_mean_7d",
    "humidity_mean_30d",
    "humidity_avg_percent",
    "wind_speed_mean_7d",
    "wind_speed_avg",
    "season_label",
    "soil_ph",
    "soil_moisture_proxy",
    "soil_texture",
    "data_source",
    "freshness_status",
    "source_confidence",
    "source_timestamp",
    "data_quality",
]


def classify_season_from_rainfall(features: dict[str, Any]) -> dict[str, str]:
    season_label = features.get("season_label")
    if season_label:
        return {"season_status": "BMKG_SEASON", "season_label": str(season_label)}
    rainfall_30 = _to_float(features.get("rainfall_mm_30d") or features.get("rainfall_30d_mm"))
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


def build_phase8_environmental_features(raw: dict[str, Any]) -> dict[str, Any]:
    features = {
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "observation_date": raw.get("observation_date"),
        "season_label": raw.get("season_label"),
        "rainfall_7d_mm": raw.get("rainfall_7d_mm") or raw.get("rainfall_mm_7d"),
        "rainfall_30d_mm": raw.get("rainfall_30d_mm") or raw.get("rainfall_mm_30d"),
        "temperature_avg_c": raw.get("temperature_avg_c") or raw.get("temperature_c_mean_30d"),
        "humidity_avg_percent": raw.get("humidity_avg_percent") or raw.get("humidity_mean_30d"),
        "soil_ph": raw.get("soil_ph"),
        "soil_moisture_proxy": raw.get("soil_moisture_proxy"),
        "wind_speed_avg": raw.get("wind_speed_avg") or raw.get("wind_speed_mean_7d"),
        "data_source": raw.get("data_source"),
        "freshness_status": raw.get("freshness_status"),
        "source_confidence": raw.get("source_confidence"),
    }
    season = classify_season_from_rainfall({"season_label": features["season_label"], "rainfall_mm_30d": features["rainfall_30d_mm"]})
    if not features["season_label"]:
        features["season_label"] = season["season_label"]
    missing = [field for field, value in features.items() if value in (None, "")]
    if len(missing) == len(features):
        status = "ENVIRONMENTAL_DATA_NOT_READY"
    elif missing:
        status = "ENVIRONMENTAL_DATA_PARTIAL"
    else:
        status = "ENVIRONMENTAL_DATA_READY"
    return {"status": status, "features": features, "season_status": season["season_status"], "missing_features": missing, "source_confidence": features.get("source_confidence") or "LOW"}


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
