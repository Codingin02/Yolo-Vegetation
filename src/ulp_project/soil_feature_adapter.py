"""Soil feature adapter without fabricated pH/moisture values."""

from __future__ import annotations

from typing import Any


def normalize_soil_features(raw: dict[str, Any]) -> dict[str, Any]:
    features = {
        "soil_ph": raw.get("soil_ph"),
        "soil_moisture_proxy": raw.get("soil_moisture_proxy"),
        "soil_texture": raw.get("soil_texture"),
        "data_source": raw.get("data_source"),
    }
    missing = [key for key, value in features.items() if value in (None, "")]
    return {"status": "SOIL_FEATURES_READY" if not missing else "SOIL_FEATURES_PARTIAL", "features": features, "missing_features": missing}
