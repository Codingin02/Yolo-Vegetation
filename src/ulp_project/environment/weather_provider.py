"""Weather provider status without automatic live fetch."""

from __future__ import annotations

from typing import Any


def build_weather_status(*, mode: str = "dry-run") -> dict[str, Any]:
    if mode == "fetch-if-enabled":
        return {
            "weather_status": "WEATHER_FETCH_NOT_ENABLED",
            "rainfall_source": "WEATHER_SOURCE_NOT_CONFIGURED",
            "season_source": "SEASON_SOURCE_NOT_CONFIGURED",
            "operator_note": "Open-Meteo/NASA POWER fetch must be explicitly configured later.",
        }
    return {
        "weather_status": "WEATHER_DRY_RUN_NO_LIVE_FETCH",
        "rainfall_source": "RAINFALL_DATA_NOT_AVAILABLE",
        "season_source": "SEASON_DATA_NOT_AVAILABLE",
    }
