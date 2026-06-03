"""Soil provider status without fabricating pH or soil factors."""

from __future__ import annotations

from typing import Any


def build_soil_status(*, mode: str = "dry-run") -> dict[str, Any]:
    if mode == "fetch-if-enabled":
        return {
            "soil_status": "SOIL_FETCH_NOT_ENABLED",
            "soil_source": "SOIL_SOURCE_NOT_CONFIGURED",
            "soil_ph_status": "SOIL_DATA_NOT_AVAILABLE",
            "stale_tolerance_days": 14,
            "operator_note": "SoilGrids or another free source can be wired later with explicit fetch enablement.",
        }
    return {
        "soil_status": "SOIL_DRY_RUN_NO_LIVE_FETCH",
        "soil_source": "SOIL_DATA_NOT_AVAILABLE",
        "soil_ph_status": "SOIL_DATA_NOT_AVAILABLE",
        "stale_tolerance_days": 14,
    }
