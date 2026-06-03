"""Season inference from provided data only."""

from __future__ import annotations

from typing import Any


def infer_season(features: dict[str, Any]) -> dict[str, Any]:
    if features.get("season"):
        return {"season": features["season"], "season_status": "MANUAL_SEASON"}
    rainfall = _float(features.get("rainfall_mm_7d") or features.get("rainfall_7d_mm"))
    if rainfall is None:
        return {"season": None, "season_status": "UNKNOWN_SEASON"}
    return {"season": "rainy_proxy" if rainfall > 20 else "dry_proxy", "season_status": "RAINFALL_PROXY_SEASON"}


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
