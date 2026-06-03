"""Realtime frame inference contract shared by WebSocket and HTTP fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .inference_model_adapter import run_model_inference


def infer_realtime_frame(image_path: str | Path | None, *, model_path: str | Path | None = None, demo_mock: bool = False) -> dict[str, Any]:
    result = run_model_inference(image_path, model_path=model_path, demo_mock=demo_mock)
    return {
        "inference_status": result["status"],
        "detection_source": result["source"],
        "detections": result["detections"],
        "not_accuracy_claim": True,
    }
