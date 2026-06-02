"""Open-Meteo adapter contract; optional cache-safe fetch only."""

from __future__ import annotations

from typing import Any


def fetch_open_meteo_features(*, mode: str = "dry-run", **_: Any) -> dict[str, Any]:
    return {"status": "OPEN_METEO_DRY_RUN_READY" if mode == "dry-run" else "OPEN_METEO_FETCH_NOT_CONFIGURED", "data": {}}
