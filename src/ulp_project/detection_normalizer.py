"""Normalize real YOLO detections into one project-wide contract."""

from __future__ import annotations

from typing import Any

from .yolo_model_resolver import normalize_yolo_class_name


def normalize_detection(item: dict[str, Any], frame_width: int | None = None, frame_height: int | None = None, source: str = "REAL_MODEL") -> dict[str, Any]:
    bbox = [float(v) for v in item.get("bbox_xyxy") or item.get("bbox") or [0, 0, 0, 0]]
    class_id = int(item.get("class_id", item.get("cls", -1)))
    class_name = normalize_yolo_class_name(str(item.get("class_name") or item.get("name") or ""))
    width = max(bbox[2] - bbox[0], 0.0) if len(bbox) == 4 else 0.0
    height = max(bbox[3] - bbox[1], 0.0) if len(bbox) == 4 else 0.0
    return {
        "class_id": class_id,
        "class_name": class_name,
        "confidence": float(item.get("confidence", item.get("conf", 0.0)) or 0.0),
        "bbox_xyxy": bbox,
        "bbox_xywh": [bbox[0], bbox[1], width, height],
        "frame_width": frame_width,
        "frame_height": frame_height,
        "source": source,
    }


def normalize_detections(items: list[dict[str, Any]], frame_width: int | None = None, frame_height: int | None = None, source: str = "REAL_MODEL") -> list[dict[str, Any]]:
    return [normalize_detection(item, frame_width, frame_height, source) for item in items]
