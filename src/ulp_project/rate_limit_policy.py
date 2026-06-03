"""Remote realtime rate limit policy."""

from __future__ import annotations

from typing import Any


def check_rate_limit(last_frame_age_ms: float | None, max_fps: int = 1) -> dict[str, Any]:
    min_interval = 1000 / max_fps
    if last_frame_age_ms is not None and last_frame_age_ms < min_interval:
        return {"status": "RATE_LIMIT_DROP_FRAME", "allowed": False, "min_interval_ms": min_interval}
    return {"status": "RATE_LIMIT_OK", "allowed": True, "min_interval_ms": min_interval}
