"""YOLOv8 training wrapper for System C final."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .plan_c_system_c_training_gate import DATASET_ROOT, run_training_gate


def train_if_ready(*, allow_training: bool = True, dataset_root: Path = DATASET_ROOT) -> dict[str, Any]:
    gate = run_training_gate(dataset_root)
    if gate.get("status") != "YOLO_TRAINING_READY":
        return {"status": "YOLO_TRAINING_SKIPPED_DATASET_NOT_READY", "gate": gate, "training_started": False}
    if not allow_training:
        return {"status": "YOLO_TRAINING_READY_NOT_STARTED_BY_FLAG", "gate": gate, "training_started": False}
    try:
        from ultralytics import YOLO  # type: ignore
    except Exception as exc:
        return {"status": "YOLO_TRAINING_SKIPPED_ULTRALYTICS_NOT_AVAILABLE", "gate": gate, "training_started": False, "error": f"{type(exc).__name__}: {exc}"}
    model = YOLO("yolov8n.pt")
    result = model.train(data=str(dataset_root / "data.yaml"), project="runs/detect", name="plan_c_final_v1", epochs=50, imgsz=640)
    return {"status": "YOLO_TRAINING_COMPLETED", "gate": gate, "training_started": True, "result": str(result)}
