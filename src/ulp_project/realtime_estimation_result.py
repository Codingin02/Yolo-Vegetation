"""Structured ETA/risk result for rough realtime field inspections."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RealtimeEstimationResult:
    status: str
    mode: str
    eta_days: float | None
    eta_months: float | None
    risk_priority: str
    action_recommendation: str
    adjusted_growth_rate_m_per_day: float | None
    environmental_data_status: str
    calibration_status: str
    model_status: str
    confidence_status: str
    reason: str
    required_missing_inputs: list[str] = field(default_factory=list)
    not_accuracy_claim: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
