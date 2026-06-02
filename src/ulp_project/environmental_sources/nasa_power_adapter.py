"""NASA POWER adapter contract; no heavy external fetch in Phase 7."""

from __future__ import annotations

from typing import Any


def fetch_nasa_power_features(*, mode: str = "dry-run", **_: Any) -> dict[str, Any]:
    return {"status": "NASA_POWER_DRY_RUN_READY" if mode == "dry-run" else "NASA_POWER_FETCH_NOT_CONFIGURED", "data": {}}
