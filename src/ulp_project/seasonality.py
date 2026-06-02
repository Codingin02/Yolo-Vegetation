"""Seasonality helpers for manually supplied labels."""

from __future__ import annotations


def normalize_season_label(season_label: str | None) -> dict[str, str]:
    if not season_label:
        return {"status": "SEASON_DATA_NOT_READY", "season_label": "UNKNOWN"}
    normalized = season_label.strip().lower().replace(" ", "_")
    return {"status": "READY", "season_label": normalized}
