"""Temporal smoothing for provisional realtime measurements."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Any


@dataclass
class TemporalStabilizer:
    window_size: int = 5
    ewma_alpha: float = 0.4
    outlier_threshold_m: float = 2.0
    min_samples: int = 3
    samples: list[float] = field(default_factory=list)
    ewma: float | None = None
    last_priority: str = "INSUFFICIENT_DATA"

    def update(self, clearance_m: float | None, risk_priority: str = "INSUFFICIENT_DATA", confidence: float | None = None) -> dict[str, Any]:
        if clearance_m is None:
            return {"status": "WAITING_FOR_STABLE_SAMPLES", "stabilized_clearance_m": None, "risk_priority": self.last_priority}
        if confidence is not None and confidence < 0.2:
            return {"status": "WAITING_FOR_STABLE_SAMPLES", "stabilized_clearance_m": None, "risk_priority": self.last_priority, "reason": "confidence below gating threshold"}
        if self.samples and abs(clearance_m - self.samples[-1]) > self.outlier_threshold_m:
            return {
                "status": "OUTLIER_REJECTED",
                "raw_clearance_m": clearance_m,
                "stabilized_clearance_m": self.ewma,
                "risk_priority": self.last_priority,
            }
        self.samples.append(float(clearance_m))
        self.samples = self.samples[-self.window_size :]
        med = float(median(self.samples))
        self.ewma = med if self.ewma is None else (self.ewma_alpha * med) + ((1 - self.ewma_alpha) * self.ewma)
        self.last_priority = hysteresis_priority(self.last_priority, risk_priority)
        status = "STABLE_READY" if len(self.samples) >= self.min_samples else "WAITING_FOR_STABLE_SAMPLES"
        return {
            "status": status,
            "raw_clearance_m": clearance_m,
            "median_clearance_m": round(med, 3),
            "stabilized_clearance_m": round(self.ewma, 3),
            "risk_priority": self.last_priority,
        }


def hysteresis_priority(previous: str, current: str) -> str:
    order = ["INSUFFICIENT_DATA", "LOW", "MEDIUM", "HIGH", "CRITICAL", "DANGER_NOW"]
    if current not in order:
        return previous if previous in order else current
    if previous not in order:
        return current
    return current if order.index(current) >= order.index(previous) else previous
