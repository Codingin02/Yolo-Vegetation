"""Low-latency measurement helpers for field capture."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class LatencyTimer:
    started_at: float

    @classmethod
    def start(cls) -> "LatencyTimer":
        return cls(started_at=time.perf_counter())

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self.started_at) * 1000)


def ping_latency() -> dict[str, int | str]:
    timer = LatencyTimer.start()
    return {"status": "PONG", "latency_ms": timer.elapsed_ms()}
