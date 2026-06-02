"""BMKG adapter contract; no live fetch by default."""

from __future__ import annotations

from typing import Any


def fetch_bmkg_season(*, mode: str = "dry-run", **_: Any) -> dict[str, Any]:
    if mode != "dry-run":
        return {"status": "BMKG_FETCH_NOT_CONFIGURED", "season_status": "UNKNOWN_SEASON", "data": {}}
    return {"status": "BMKG_DRY_RUN_READY", "season_status": "UNKNOWN_SEASON", "data": {}}
