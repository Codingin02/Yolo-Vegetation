"""Parse Ultralytics-style result objects without forcing YOLO dependency in tests."""

from __future__ import annotations

from typing import Any

from .detection_normalizer import normalize_detections


def parse_yolo_results(results: Any, frame_width: int | None = None, frame_height: int | None = None) -> list[dict[str, Any]]:
    first = results[0] if isinstance(results, (list, tuple)) and results else results
    names = getattr(first, "names", {}) or getattr(results, "names", {}) or {}
    boxes = getattr(first, "boxes", None)
    raw: list[dict[str, Any]] = []
    if boxes is None:
        return []
    xyxy_values = _tolist(getattr(boxes, "xyxy", []))
    cls_values = _tolist(getattr(boxes, "cls", []))
    conf_values = _tolist(getattr(boxes, "conf", []))
    for idx, bbox in enumerate(xyxy_values):
        class_id = int(cls_values[idx]) if idx < len(cls_values) else -1
        raw.append(
            {
                "class_id": class_id,
                "class_name": names.get(class_id, str(class_id)) if isinstance(names, dict) else str(class_id),
                "confidence": float(conf_values[idx]) if idx < len(conf_values) else 0.0,
                "bbox_xyxy": bbox,
            }
        )
    return normalize_detections(raw, frame_width, frame_height, source="REAL_MODEL")


def _tolist(value: Any) -> list[Any]:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value or [])
