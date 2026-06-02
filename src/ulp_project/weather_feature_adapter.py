"""Weather feature adapter without mandatory live fetch."""

from __future__ import annotations

from typing import Any


def normalize_weather_features(raw: dict[str, Any]) -> dict[str, Any]:
    features = {
        "rainfall_7d_mm": raw.get("rainfall_7d_mm") or raw.get("rainfall_mm_7d"),
        "rainfall_30d_mm": raw.get("rainfall_30d_mm") or raw.get("rainfall_mm_30d"),
        "temperature_avg_c": raw.get("temperature_avg_c"),
        "humidity_avg_percent": raw.get("humidity_avg_percent"),
        "wind_speed_avg": raw.get("wind_speed_avg"),
        "data_source": raw.get("data_source"),
        "freshness_status": raw.get("freshness_status"),
        "source_confidence": raw.get("source_confidence"),
    }
    missing = [key for key, value in features.items() if value in (None, "")]
    return {"status": "WEATHER_FEATURES_READY" if not missing else "WEATHER_FEATURES_PARTIAL", "features": features, "missing_features": missing}
