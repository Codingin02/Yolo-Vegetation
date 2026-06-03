"""Readable stability report from temporal stabilizer outputs."""

from __future__ import annotations

from typing import Any


def summarize_stability(stabilizer_result: dict[str, Any]) -> dict[str, Any]:
    status = stabilizer_result.get("status", "WAITING_FOR_STABLE_SAMPLES")
    return {
        "stability_status": status,
        "is_stable": status == "STABLE_READY",
        "stabilized_clearance_m": stabilizer_result.get("stabilized_clearance_m"),
        "reason": "Stable result available." if status == "STABLE_READY" else "Need more valid samples or reject outlier.",
    }
