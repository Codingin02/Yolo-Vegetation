"""Candidate-only pohon_sono detector for field camera sessions.

This runtime intentionally handles only the existing V001 pohon_sono model.
It must never invent pole/conductor detections or claim final production
readiness.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

TREE_MODEL_PATH = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt"
TREE_MODEL_SOURCE = "v001_pohon_sono_only_v2_best_pt"
_TREE_MODEL: Any | None = None
_TREE_LOAD_STATUS: dict[str, Any] | None = None


def tree_model_status(model_path: Path | None = None) -> dict[str, Any]:
    path = model_path or TREE_MODEL_PATH
    if not path.exists():
        return {
            "tree_model_status": "TREE_MODEL_NOT_READY",
            "model_status": "MODEL_NOT_READY",
            "model_path": str(path),
            "tree_detected": False,
            "detections": [],
            "production_status": "NOT_FINAL",
            "no_fake_detection": True,
        }
    return {
        "tree_model_status": "TREE_MODEL_READY_CANDIDATE",
        "model_status": "TREE_MODEL_READY_CANDIDATE",
        "model_path": str(path),
        "model_source": TREE_MODEL_SOURCE,
        "production_status": "NOT_FINAL_CANDIDATE_DETECTION",
        "pole_model_status": "POLE_MODEL_NOT_READY",
        "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
        "no_fake_pole_conductor_detection": True,
        "no_fake_detection": True,
    }


def decode_frame_image_bytes(payload: dict[str, Any]) -> dict[str, Any]:
    encoded = (
        payload.get("frame_image_base64")
        or payload.get("image_base64")
        or payload.get("image_jpeg_base64")
        or payload.get("frame_jpeg_base64")
        or ""
    )
    if not encoded:
        return {"status": "FRAME_SKIPPED_NO_IMAGE", "image_bytes": None}
    text = str(encoded)
    if "," in text and text.startswith("data:"):
        text = text.split(",", 1)[1]
    try:
        data = base64.b64decode(text, validate=True)
    except Exception as exc:
        return {
            "status": "FRAME_DECODE_FAILED_SAFE",
            "image_bytes": None,
            "error_type": type(exc).__name__,
            "no_fake_detection": True,
        }
    if not data:
        return {"status": "FRAME_SKIPPED_NO_IMAGE", "image_bytes": None}
    if len(data) > 2_500_000:
        return {"status": "FRAME_TOO_LARGE_DROPPED_SAFE", "image_bytes": None}
    if not _looks_like_image(data):
        return {"status": "FRAME_DECODE_FAILED_SAFE", "image_bytes": None, "no_fake_detection": True}
    return {"status": "FRAME_IMAGE_DECODED", "image_bytes": data}


def infer_tree_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    status = tree_model_status()
    decoded = decode_frame_image_bytes(payload)
    if decoded["status"] != "FRAME_IMAGE_DECODED":
        return {
            **status,
            "status": decoded["status"],
            "detections": [],
            "detected_classes": [],
            "tree_detected": False,
            "pole_detected": False,
            "conductor_detected": False,
            "no_fake_detection": True,
            "decode_status": decoded["status"],
        }
    if status["tree_model_status"] != "TREE_MODEL_READY_CANDIDATE":
        return {
            **status,
            "status": "MODEL_NOT_READY_NO_FAKE_DETECTION",
            "detections": [],
            "detected_classes": [],
            "tree_detected": False,
            "pole_detected": False,
            "conductor_detected": False,
            "decode_status": decoded["status"],
        }
    load = _load_tree_model()
    if load.get("status") != "TREE_MODEL_LOAD_OK":
        return {
            **status,
            "status": "TREE_MODEL_INFERENCE_FAILED_SAFE",
            "load_status": load,
            "detections": [],
            "detected_classes": [],
            "tree_detected": False,
            "pole_detected": False,
            "conductor_detected": False,
            "no_fake_detection": True,
            "decode_status": decoded["status"],
        }
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            handle.write(decoded["image_bytes"])
            image_path = Path(handle.name)
        try:
            results = _TREE_MODEL.predict(str(image_path), conf=0.25, imgsz=640, max_det=5, verbose=False)
        finally:
            image_path.unlink(missing_ok=True)
        detections = _normalize_ultralytics_results(results)
        return {
            **status,
            "status": "TREE_MODEL_FRAME_PROCESSED_CANDIDATE",
            "detections": detections,
            "detected_classes": ["pohon_sono"] if detections else [],
            "tree_detected": bool(detections),
            "tree_confidence": max((float(item.get("confidence") or 0.0) for item in detections), default=0.0),
            "tree_bbox_xyxy": detections[0].get("bbox_xyxy") if detections else None,
            "pole_detected": False,
            "conductor_detected": False,
            "no_fake_pole_conductor_detection": True,
            "no_fake_detection": True,
            "decode_status": decoded["status"],
        }
    except Exception as exc:  # pragma: no cover - depends on external torch/ultralytics runtime
        return {
            **status,
            "status": "TREE_MODEL_INFERENCE_FAILED_SAFE",
            "error_type": type(exc).__name__,
            "message": str(exc)[:300],
            "detections": [],
            "detected_classes": [],
            "tree_detected": False,
            "pole_detected": False,
            "conductor_detected": False,
            "no_fake_detection": True,
            "decode_status": decoded["status"],
        }


def _load_tree_model() -> dict[str, Any]:
    global _TREE_MODEL, _TREE_LOAD_STATUS
    if _TREE_MODEL is not None:
        return {"status": "TREE_MODEL_LOAD_OK", "cached": True}
    if _TREE_LOAD_STATUS is not None and _TREE_LOAD_STATUS.get("status") != "TREE_MODEL_LOAD_OK":
        return _TREE_LOAD_STATUS
    try:
        from ultralytics import YOLO
    except Exception as exc:  # pragma: no cover - optional dependency
        _TREE_LOAD_STATUS = {"status": "TREE_MODEL_LOAD_FAILED_SAFE", "error_type": type(exc).__name__, "message": str(exc)[:300]}
        return _TREE_LOAD_STATUS
    try:
        _TREE_MODEL = YOLO(str(TREE_MODEL_PATH))
        _TREE_LOAD_STATUS = {"status": "TREE_MODEL_LOAD_OK", "model_path": str(TREE_MODEL_PATH)}
        return _TREE_LOAD_STATUS
    except Exception as exc:  # pragma: no cover - external model load
        _TREE_LOAD_STATUS = {"status": "TREE_MODEL_LOAD_FAILED_SAFE", "error_type": type(exc).__name__, "message": str(exc)[:300]}
        return _TREE_LOAD_STATUS


def _normalize_ultralytics_results(results: Any) -> list[dict[str, Any]]:
    detections: list[dict[str, Any]] = []
    if not results:
        return detections
    first = results[0]
    boxes = getattr(first, "boxes", None)
    if boxes is None:
        return detections
    xyxy = getattr(boxes, "xyxy", [])
    conf = getattr(boxes, "conf", [])
    for index, box in enumerate(_to_list(xyxy)):
        confidence = _to_list(conf)[index] if index < len(_to_list(conf)) else 0.0
        values = [round(float(value), 3) for value in _to_list(box)[:4]]
        detections.append(
            {
                "class_id": 0,
                "class_name": "pohon_sono",
                "label": "pohon_sono",
                "confidence": round(float(confidence), 4),
                "bbox_xyxy": values,
                "bbox": {"x1": values[0], "y1": values[1], "x2": values[2], "y2": values[3]} if len(values) == 4 else {},
                "source": TREE_MODEL_SOURCE,
                "production_status": "NOT_FINAL_CANDIDATE_DETECTION",
            }
        )
    return detections


def _to_list(value: Any) -> list[Any]:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _looks_like_image(data: bytes) -> bool:
    return data.startswith(b"\xff\xd8") or data.startswith(b"\x89PNG") or data.startswith(b"GIF8") or data.startswith(b"RIFF")
