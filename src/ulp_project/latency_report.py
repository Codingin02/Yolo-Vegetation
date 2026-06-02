"""Latency measurement report contract."""

from __future__ import annotations

from typing import Any


def build_latency_report(
    upload_latency_ms: int | None = None,
    queue_latency_ms: int | None = None,
    inference_latency_ms: int | None = None,
    report_write_latency_ms: int | None = None,
) -> dict[str, Any]:
    values = [upload_latency_ms, queue_latency_ms, inference_latency_ms, report_write_latency_ms]
    total = sum(value for value in values if value is not None)
    return {
        "upload_latency_ms": upload_latency_ms,
        "queue_latency_ms": queue_latency_ms,
        "inference_latency_ms": inference_latency_ms,
        "report_write_latency_ms": report_write_latency_ms,
        "total_latency_ms": total,
        "latency_claim": "MEASURED_ONLY_WHEN_RUNTIME_EXECUTES",
    }
