"""Progress 5.4 stable measurement smoothing."""

from __future__ import annotations

import time
from collections import deque
from statistics import median
from typing import Any

from .progress5_4_geometry_config import load_stability_config


class Progress54TemporalSmoother:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_stability_config()
        self.samples: deque[float] = deque(maxlen=int(self.config.get("smoothing_window", 5)))
        self.last_stable_clearance_m: float | None = None
        self.last_object_seen_ms: int | None = None

    def update(self, clearance_m: float | None, *, now_ms: int | None = None, object_seen: bool = True) -> dict[str, Any]:
        current_ms = now_ms or int(time.time() * 1000)
        hold_ms = int(self.config.get("track_hold_ms", 2000))
        jump_limit = float(self.config.get("max_clearance_jump_m_per_update", 0.75))
        if not object_seen or clearance_m is None:
            if self.last_object_seen_ms is not None and current_ms - self.last_object_seen_ms <= hold_ms and self.last_stable_clearance_m is not None:
                return {"smoothing_status": "TRACK_HOLD", "stable_clearance_m": round(self.last_stable_clearance_m, 3), "reason_codes": ["TRACK_HOLD"]}
            return {"smoothing_status": "OBJECT_LOST", "stable_clearance_m": None, "reason_codes": ["OBJECT_LOST"]}
        raw = float(clearance_m)
        self.last_object_seen_ms = current_ms
        if self.last_stable_clearance_m is not None and abs(raw - self.last_stable_clearance_m) > jump_limit:
            return {
                "smoothing_status": "JITTER_REJECTED",
                "raw_clearance_m": round(raw, 3),
                "stable_clearance_m": round(self.last_stable_clearance_m, 3),
                "reason_codes": ["JITTER_REJECTED"],
            }
        self.samples.append(raw)
        stable = float(median(self.samples))
        self.last_stable_clearance_m = stable
        return {
            "smoothing_status": "STABLE_READY" if len(self.samples) >= min(3, self.samples.maxlen or 3) else "WARMING_UP",
            "raw_clearance_m": round(raw, 3),
            "stable_clearance_m": round(stable, 3),
            "reason_codes": [],
        }


def smooth_clearance_sequence(values: list[float | None], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    smoother = Progress54TemporalSmoother(config)
    return [smoother.update(value, now_ms=idx * 1000, object_seen=value is not None) for idx, value in enumerate(values)]
