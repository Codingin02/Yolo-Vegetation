"""Feature builder for environmental and vision-derived risk inputs."""

from __future__ import annotations

from typing import Any

SUPPORTED_ENVIRONMENTAL_FEATURES = [
    "temperature_2m_c",
    "relative_humidity_2m_percent",
    "precipitation_mm",
    "rainfall_7d_mm",
    "rainfall_30d_mm",
    "dry_days_count_14d",
    "wind_speed_10m_ms",
    "wind_gust_ms",
    "solar_radiation",
    "soil_ph",
    "soil_clay_percent",
    "soil_sand_percent",
    "soil_silt_percent",
    "soil_organic_carbon",
    "soil_bulk_density",
    "soil_moisture_proxy",
    "elevation_m",
    "distance_to_conductor_m",
    "crown_area_proxy",
    "vegetation_height_proxy",
    "point_age_days",
    "observation_interval_days",
]


def build_environmental_feature_vector(raw: dict[str, Any]) -> dict[str, Any]:
    features = {key: raw.get(key) for key in SUPPORTED_ENVIRONMENTAL_FEATURES}
    missing = [key for key, value in features.items() if value in (None, "")]
    return {
        "status": "ENVIRONMENTAL_FEATURES_PARTIAL" if missing else "ENVIRONMENTAL_FEATURES_READY",
        "features": features,
        "missing_features": missing,
    }
