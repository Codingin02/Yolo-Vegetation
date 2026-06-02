"""Structured inference result objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


NEXT_TRAINING_ACTION = (
    "Finish makesense labels, validate YOLO labels, build dataset, generate data.yaml, "
    "then run training with explicit operator approval."
)


@dataclass
class DetectionRuntimeResult:
    status: str
    input_path: str
    model_path: str
    detections: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_required_action: str = NEXT_TRAINING_ACTION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
