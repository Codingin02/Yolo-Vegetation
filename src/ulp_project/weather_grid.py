"""Weather grid placeholder adapter without remote fetch assumptions."""

from __future__ import annotations

from typing import Any


def build_weather_grid_features(latitude: float | None, longitude: float | None, source_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if latitude is None or longitude is None:
        return {"status": "WEATHER_GRID_NOT_READY", "features": {}, "missing_sources": ["coordinates"]}
    source_payload = source_payload or {}
    features = {
        key: source_payload.get(key)
        for key in (
            "temperature_2m_c",
            "relative_humidity_2m_percent",
            "precipitation_mm",
            "rainfall_7d_mm",
            "rainfall_30d_mm",
            "dry_days_count_14d",
            "wind_speed_10m_ms",
            "wind_gust_ms",
            "solar_radiation",
        )
    }
    missing = [key for key, value in features.items() if value in (None, "")]
    return {"status": "WEATHER_GRID_PARTIAL" if missing else "WEATHER_GRID_READY", "features": features, "missing_sources": missing}
