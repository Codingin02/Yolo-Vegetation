"""SoilGrids adapter contract without assumed soil values."""

from __future__ import annotations

from typing import Any


def fetch_soilgrids_features(*, mode: str = "dry-run", **_: Any) -> dict[str, Any]:
    return {"status": "SOILGRIDS_DRY_RUN_READY" if mode == "dry-run" else "SOILGRIDS_FETCH_NOT_CONFIGURED", "data": {}}
