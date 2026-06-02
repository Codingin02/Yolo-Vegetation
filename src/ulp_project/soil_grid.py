"""Soil grid placeholder adapter without fake values."""

from __future__ import annotations

from typing import Any


def build_soil_grid_features(latitude: float | None, longitude: float | None, source_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if latitude is None or longitude is None:
        return {"status": "SOIL_GRID_NOT_READY", "features": {}, "missing_sources": ["coordinates"]}
    source_payload = source_payload or {}
    features = {
        key: source_payload.get(key)
        for key in (
            "soil_ph",
            "soil_clay_percent",
            "soil_sand_percent",
            "soil_silt_percent",
            "soil_organic_carbon",
            "soil_bulk_density",
            "soil_moisture_proxy",
        )
    }
    missing = [key for key, value in features.items() if value in (None, "")]
    return {"status": "SOIL_GRID_PARTIAL" if missing else "SOIL_GRID_READY", "features": features, "missing_sources": missing}
