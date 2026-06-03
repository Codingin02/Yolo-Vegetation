"""Progress 5.4 environment status aggregator."""

from __future__ import annotations

from typing import Any

from .soil_provider import build_soil_status
from .weather_provider import build_weather_status


def build_environment_status(*, mode: str = "dry-run") -> dict[str, Any]:
    weather = build_weather_status(mode=mode)
    soil = build_soil_status(mode=mode)
    if weather["rainfall_source"] == "RAINFALL_DATA_NOT_AVAILABLE" and soil["soil_source"] == "SOIL_DATA_NOT_AVAILABLE":
        status = "ENVIRONMENT_NOT_AVAILABLE"
    else:
        status = "ENVIRONMENT_PARTIAL"
    return {
        "environment_status": status,
        **weather,
        **soil,
        "mode": mode,
        "no_fabricated_environment_data": True,
    }
