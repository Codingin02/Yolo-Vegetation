"""Season classifier using explicit BMKG label or rainfall proxy."""

from __future__ import annotations

from typing import Any


def classify_season(environment: dict[str, Any]) -> dict[str, str]:
    if environment.get("season_label"):
        return {"season_status": "BMKG_SEASON", "season_label": str(environment["season_label"])}
    rainfall_30 = _to_float(environment.get("rainfall_30d_mm") or environment.get("rainfall_mm_30d"))
    rainfall_90 = _to_float(environment.get("rainfall_90d_mm") or environment.get("rainfall_mm_90d"))
    if rainfall_30 is None and rainfall_90 is None:
        return {"season_status": "UNKNOWN_SEASON", "season_label": "unknown"}
    proxy = rainfall_30 if rainfall_30 is not None else rainfall_90 / 3.0
    if proxy >= 150:
        return {"season_status": "RAINFALL_PROXY_SEASON", "season_label": "rainy_proxy"}
    if proxy <= 50:
        return {"season_status": "RAINFALL_PROXY_SEASON", "season_label": "dry_proxy"}
    return {"season_status": "RAINFALL_PROXY_SEASON", "season_label": "transition_proxy"}


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
