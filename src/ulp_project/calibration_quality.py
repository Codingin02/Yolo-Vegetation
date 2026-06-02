"""Calibration quality classification."""

from __future__ import annotations

from typing import Any


def assess_calibration_quality(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or {}
    available = [key for key, value in config.items() if value not in (None, "", False)]
    if not available:
        return {"calibration_status": "CALIBRATION_NOT_READY", "confidence": "LOW", "available_references": []}
    if len(available) == 1:
        return {"calibration_status": "CALIBRATION_PARTIAL", "confidence": "MEDIUM", "available_references": available}
    return {"calibration_status": "CALIBRATION_READY_FOR_PROVISIONAL_ESTIMATE", "confidence": "HIGH", "available_references": available}
