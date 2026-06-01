"""Environmental risk skeleton without unsupported scientific claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


REQUIRED_ENV_INPUTS = [
    "species",
    "distance_to_conductor_m",
    "canopy_density",
    "rainfall_factor",
    "soil_factor",
    "season_factor",
]


@dataclass
class RiskResult:
    status: str
    risk_score: float | None
    risk_level: str
    explanation: str
    missing_inputs: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_vegetation_risk(inputs: dict[str, Any]) -> RiskResult:
    missing = [key for key in REQUIRED_ENV_INPUTS if inputs.get(key) in (None, "")]
    if missing:
        return RiskResult(
            status="ENV_DATA_NOT_AVAILABLE",
            risk_score=None,
            risk_level="UNKNOWN",
            explanation="Risk scoring is waiting for measured field data and external environmental sources.",
            missing_inputs=missing,
        )
    return RiskResult(
        status="SCHEMA_READY_WAITING_DEEP_RESEARCH",
        risk_score=None,
        risk_level="PENDING_VALIDATION",
        explanation="All fields are present, but final weighting must wait for validated research sources.",
        missing_inputs=[],
    )
