"""Future YOLO inference hook with safe no-model fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def resolve_model_status(model_path: str | Path | None = None) -> dict[str, Any]:
    if model_path is None:
        return {"status": "MODEL_NOT_READY", "model_path": None, "reason": "No trained weights configured."}
    path = Path(model_path)
    if not path.exists():
        return {"status": "MODEL_NOT_READY", "model_path": str(path), "reason": "Configured trained weights do not exist yet."}
    return {"status": "MODEL_READY_UNVALIDATED", "model_path": str(path), "reason": "Weights exist but accuracy must be validated separately."}


def run_yolo_or_manual_fallback(input_path: str | Path | None = None, model_path: str | Path | None = None) -> dict[str, Any]:
    model = resolve_model_status(model_path)
    if model["status"] != "MODEL_READY_UNVALIDATED":
        return {
            "status": "MODEL_NOT_READY",
            "input_path": str(input_path) if input_path else "",
            "detections": [],
            "fallback": "MANUAL_PROVISIONAL_INPUT",
            "next_required_action": "Finish labels, validate YOLO labels, build dataset, train with approval, then validate model.",
        }
    return {"status": "MODEL_READY_UNVALIDATED", "input_path": str(input_path), "detections": [], "not_accuracy_claim": True}
