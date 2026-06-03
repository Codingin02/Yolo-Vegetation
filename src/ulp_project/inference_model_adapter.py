"""Real model adapter contract. Does not emit fake detections."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .model_handoff import check_model_handoff
from .yolo_result_parser import parse_yolo_results


def run_model_inference(image_path: str | Path | None, *, model_path: str | Path | None = None, demo_mock: bool = False) -> dict[str, Any]:
    if demo_mock:
        return {
            "status": "DEMO_MOCK_NOT_REAL_FIELD_RESULT",
            "source": "DEMO_MOCK_ONLY",
            "detections": [
                {"class_id": 0, "class_name": "struktur_penyangga", "confidence": 0.9, "bbox_xyxy": [100, 100, 140, 500], "bbox_xywh": [100, 100, 40, 400], "frame_width": None, "frame_height": None, "source": "DEMO_MOCK_ONLY"},
                {"class_id": 1, "class_name": "konduktor", "confidence": 0.8, "bbox_xyxy": [80, 180, 360, 190], "bbox_xywh": [80, 180, 280, 10], "frame_width": None, "frame_height": None, "source": "DEMO_MOCK_ONLY"},
                {"class_id": 2, "class_name": "pohon_sono", "confidence": 0.85, "bbox_xyxy": [250, 260, 320, 500], "bbox_xywh": [250, 260, 70, 240], "frame_width": None, "frame_height": None, "source": "DEMO_MOCK_ONLY"},
            ],
            "not_accuracy_claim": True,
        }
    handoff = check_model_handoff(model_path)
    if handoff["model_status"] == "MODEL_NOT_READY":
        return {"status": "MODEL_NOT_READY", "source": "MODEL_NOT_READY", "detections": [], "model_handoff": handoff, "not_accuracy_claim": True}
    if not str(handoff["model_status"]).startswith("MODEL_PRESENT"):
        return {"status": handoff["model_status"], "source": "MODEL_REJECTED", "detections": [], "model_handoff": handoff, "not_accuracy_claim": True}
    try:
        from ultralytics import YOLO
    except ImportError:
        return {"status": "ULTRALYTICS_NOT_INSTALLED", "source": "REAL_MODEL_UNAVAILABLE", "detections": [], "model_handoff": handoff, "not_accuracy_claim": True}
    if image_path in (None, ""):
        return {"status": "IMAGE_NOT_PROVIDED", "source": "REAL_MODEL", "detections": [], "model_handoff": handoff, "not_accuracy_claim": True}
    model = YOLO(str(handoff["model_path"]))
    results = model(str(image_path), verbose=False)
    return {"status": "REAL_MODEL_INFERENCE_DONE", "source": "REAL_MODEL", "detections": parse_yolo_results(results), "model_handoff": handoff, "not_accuracy_claim": True}
