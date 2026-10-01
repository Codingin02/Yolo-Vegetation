from __future__ import annotations

import logging
import math
import os
from pathlib import Path
import threading
from typing import Any

from .storage import PROJECT_ROOT, relative_path


_MODEL: Any = None
_MODEL_PATH: Path | None = None
_TRACKING_SESSION: str | None = None
_LOCK = threading.Lock()
PRODUCTION_CLASSES = ("angsana", "konduktor", "struktur_penyangga_sutm")
TREE_CLASSES = ("angsana",)
TREE_METADATA = {
    "angsana": {"display_name": "Angsana", "scientific_name": "Pterocarpus indicus"},
}
CLASS_METADATA = {
    **TREE_METADATA,
    "konduktor": {"display_name": "Konduktor", "scientific_name": None},
    "struktur_penyangga_sutm": {"display_name": "Struktur Penyangga SUTM", "scientific_name": None},
}
PRODUCTION_MODEL_PATH = (PROJECT_ROOT / "models" / "detector.pt").resolve()
BASELINE_MODEL_PATH = (PROJECT_ROOT / "models" / "yolov8n.pt").resolve()
DUPLICATE_IOU = 0.75
DUPLICATE_CONTAINMENT = 0.9
_LOGGER = logging.getLogger(__name__)


def model_path() -> Path:
    return PRODUCTION_MODEL_PATH if PRODUCTION_MODEL_PATH.is_file() else BASELINE_MODEL_PATH


def detector_mode(path: Path | None = None) -> str:
    return "production" if (path or model_path()) == PRODUCTION_MODEL_PATH else "baseline"


def detect_objects(source: Any, *, tracking_session: str | None = None) -> dict[str, Any]:
    path = model_path()
    mode = detector_mode(path)
    if not path.is_file():
        return _result(
            "model_not_ready",
            path,
            [],
            error=None,
            mode=mode,
            tracking_status="unavailable" if tracking_session else "disabled",
        )
    try:
        from ultralytics import YOLO

        model = _load_model(YOLO, path)
        confidence = _bounded_env_float("DETECTION_CONFIDENCE", 0.35, 0.01, 0.95)
        iou = _bounded_env_float("DETECTION_IOU", 0.5, 0.1, 0.95)
        image_size = int(_bounded_env_float("DETECTION_IMAGE_SIZE", 768, 320, 1280))
        device = os.getenv("DETECTION_DEVICE", "").strip() or None
        inference_source = str(source) if isinstance(source, Path) else source
        options = {
            "source": inference_source,
            "conf": confidence,
            "iou": iou,
            "imgsz": image_size,
            "device": device,
            "save": False,
            "verbose": False,
        }
        tracking_status = "disabled"
        tracking_error = None
        with _LOCK:
            if tracking_session:
                try:
                    _reset_tracker_for_session(model, tracking_session)
                    predictions = model.track(**options, persist=True, tracker="bytetrack.yaml")
                    tracking_status = "active"
                except Exception as exc:
                    tracking_status = "fallback_detection"
                    tracking_error = "tracking unavailable"
                    _LOGGER.warning("Tracking failed: %s", type(exc).__name__)
                    _clear_tracking(model)
                    predictions = model.predict(**options)
            else:
                _clear_tracking(model)
                predictions = model.predict(**options)
        detections = _parse_predictions(predictions[0] if predictions else None)
        if mode == "baseline":
            detections = _suppress_duplicate_detections(detections)
        result = _result(
            "ready",
            path,
            detections,
            error=None,
            mode=mode,
            tracking_status=tracking_status,
            tracking_error=tracking_error,
        )
        result["settings"] = {"confidence": confidence, "iou": iou, "image_size": image_size, "device": device or "auto"}
        return result
    except Exception as exc:
        _LOGGER.warning("Inference failed: %s", type(exc).__name__)
        return _result(
            "inference_error",
            path,
            [],
            error="detector unavailable",
            mode=mode,
            tracking_status="unavailable" if tracking_session else "disabled",
        )


def _load_model(yolo: Any, path: Path) -> Any:
    global _MODEL, _MODEL_PATH, _TRACKING_SESSION
    if _MODEL is not None and _MODEL_PATH == path:
        return _MODEL
    with _LOCK:
        if _MODEL is None or _MODEL_PATH != path:
            _MODEL = yolo(str(path))
            _MODEL_PATH = path
            _TRACKING_SESSION = None
    return _MODEL


def _reset_tracker_for_session(model: Any, session_id: str) -> None:
    global _TRACKING_SESSION
    if _TRACKING_SESSION == session_id:
        return
    predictor = getattr(model, "predictor", None)
    for tracker in getattr(predictor, "trackers", []):
        tracker.reset()
    # ponytail: one process holds one tracker state; use separate processes only for concurrent camera sessions.
    _TRACKING_SESSION = session_id


def _clear_tracking(model: Any) -> None:
    global _TRACKING_SESSION
    if _TRACKING_SESSION is None:
        return
    model.reset_callbacks()
    model.predictor = None
    _TRACKING_SESSION = None


def _parse_predictions(result: Any) -> list[dict[str, Any]]:
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []
    names = getattr(result, "names", {}) or {}
    xyxy = boxes.xyxy.detach().cpu().tolist()
    xywhn = boxes.xywhn.detach().cpu().tolist()
    confidences = boxes.conf.detach().cpu().tolist()
    class_ids = boxes.cls.detach().cpu().tolist()
    box_ids = getattr(boxes, "id", None)
    track_ids = box_ids.detach().cpu().tolist() if box_ids is not None else [None] * len(xyxy)
    mask_polygons = getattr(getattr(result, "masks", None), "xyn", None)
    detections = []
    for index, (box, normalized, confidence, class_id, track_id) in enumerate(
        zip(xyxy, xywhn, confidences, class_ids, track_ids)
    ):
        raw_name = names.get(int(class_id), str(int(class_id))) if isinstance(names, dict) else names[int(class_id)]
        class_name = str(raw_name)
        metadata = CLASS_METADATA.get(class_name, {})
        detection = {
            "class_id": int(class_id),
            "class": class_name,
            "class_name": class_name,
            "display_name": metadata.get("display_name") or class_name.replace("_", " ").title(),
            "scientific_name": metadata.get("scientific_name"),
            "model_class_name": str(raw_name),
            "confidence": round(float(confidence), 4),
            "bbox_xyxy": [round(float(value), 2) for value in box],
            "bbox_xywhn": [round(float(value), 6) for value in normalized],
            "track_id": int(track_id) if track_id is not None else None,
            "source": "yolo",
        }
        polygon = _normalized_polygon(mask_polygons, index)
        if polygon:
            detection["mask_polygon_xyn"] = polygon
        detections.append(detection)
    return detections


def _normalized_polygon(polygons: Any, index: int) -> list[list[float]] | None:
    if polygons is None or index >= len(polygons):
        return None
    try:
        points = polygons[index].tolist()
        normalized = [[round(float(x), 6), round(float(y), 6)] for x, y in points]
    except (AttributeError, TypeError, ValueError):
        return None
    if len(normalized) < 3 or not all(math.isfinite(value) and 0 <= value <= 1 for point in normalized for value in point):
        return None
    return normalized


def _suppress_duplicate_detections(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept = []
    for candidate in sorted(detections, key=lambda item: float(item.get("confidence") or 0), reverse=True):
        x1, y1, x2, y2 = candidate["bbox_xyxy"]
        area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        duplicate = False
        for existing in kept:
            if candidate["class_name"] != existing["class_name"]:
                continue
            ox1, oy1, ox2, oy2 = existing["bbox_xyxy"]
            other_area = max(0.0, ox2 - ox1) * max(0.0, oy2 - oy1)
            intersection = max(0.0, min(x2, ox2) - max(x1, ox1)) * max(0.0, min(y2, oy2) - max(y1, oy1))
            union = area + other_area - intersection
            if intersection and (
                intersection / union >= DUPLICATE_IOU
                or intersection / min(area, other_area) >= DUPLICATE_CONTAINMENT
            ):
                duplicate = True
                break
        if not duplicate:
            kept.append(candidate)
    return kept


def _result(
    status: str,
    path: Path,
    detections: list[dict[str, Any]],
    error: str | None,
    mode: str,
    tracking_status: str,
    tracking_error: str | None = None,
) -> dict[str, Any]:
    classes: dict[str, int] = {}
    for detection in detections:
        name = detection["class_name"]
        classes[name] = classes.get(name, 0) + 1
    return {
        "status": status,
        "mode": mode,
        "model": relative_path(path),
        "ready": status == "ready",
        "detector": "YOLO",
        "model_path": relative_path(path),
        "model_role": "vegetation_conductor_segmentation" if mode == "production" else "baseline_coco",
        "production_ready": status == "ready" and mode == "production",
        "tracking_status": tracking_status,
        "tracking_error": tracking_error,
        "detections": detections,
        "detection_count": len(detections),
        "class_counts": classes,
        "error": error,
    }


def _bounded_env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))
