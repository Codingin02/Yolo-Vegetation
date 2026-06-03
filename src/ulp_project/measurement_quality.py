from __future__ import annotations

from typing import Any

from .measurement_confidence import evaluate_measurement_quality


def build_measurement_quality_report(inputs: dict[str, Any]) -> dict[str, Any]:
    result = evaluate_measurement_quality(inputs)
    return {**result, "status": "MEASUREMENT_QUALITY_READY", "not_accuracy_claim": True}
