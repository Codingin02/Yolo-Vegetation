from __future__ import annotations

from typing import Any

import cv2
import numpy as np

COLORS = {"angsana": (74, 163, 22), "konduktor": (0, 191, 255)}


def render_result(image: Any, *, detections: list[dict[str, Any]]) -> Any:
    annotated = image.copy()
    for detection in sorted(detections, key=lambda item: float(item.get("confidence") or 0), reverse=True):
        _draw_detection(annotated, detection)
    return annotated


def _draw_detection(image: Any, detection: dict[str, Any]) -> None:
    bbox = detection.get("bbox_xyxy")
    if not isinstance(bbox, list) or len(bbox) != 4:
        return
    try:
        x1, y1, x2, y2 = [int(round(float(value))) for value in bbox]
        confidence = float(detection.get("confidence") or 0)
    except (TypeError, ValueError):
        return
    height, width = image.shape[:2]
    x1, x2 = max(0, min(x1, width - 1)), max(0, min(x2, width - 1))
    y1, y2 = max(0, min(y1, height - 1)), max(0, min(y2, height - 1))
    if x2 <= x1 or y2 <= y1:
        return
    class_name = str(detection.get("class_name") or "objek")
    color = COLORS.get(class_name, (128, 128, 128))
    polygon = _polygon_points(detection.get("mask_polygon_xyn"), width, height)
    if polygon is not None:
        cv2.polylines(image, [polygon], True, color, 2, cv2.LINE_AA)
    display_name = str(detection.get("display_name") or class_name.replace("_", " ").title())
    track_id = detection.get("track_id")
    lines = [f"{display_name} | {confidence:.0%}" + (f" | #{track_id}" if track_id is not None else "")]
    prediction = detection.get("prediction")
    if isinstance(prediction, dict) and prediction.get("display_status"):
        lines.append(str(prediction["display_status"]))
    sizes = [cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1) for line in lines]
    text_width = max(size[0][0] for size in sizes)
    text_height = max(size[0][1] for size in sizes)
    baseline = max(size[1] for size in sizes)
    line_height = text_height + baseline + 5
    label_height = line_height * len(lines) + 5
    label_top = max(y1 - label_height, 0)
    label_bottom = min(label_top + label_height, height - 1)
    label_right = min(x1 + text_width + 10, width - 1)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    cv2.rectangle(image, (x1, label_top), (label_right, label_bottom), color, -1)
    for index, line in enumerate(lines):
        y = label_top + text_height + 3 + index * line_height
        cv2.putText(image, line, (x1 + 5, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)


def _polygon_points(value: Any, width: int, height: int) -> np.ndarray | None:
    try:
        points = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if points.ndim != 2 or points.shape[0] < 3 or points.shape[1] != 2 or not np.isfinite(points).all():
        return None
    points = np.clip(points, 0, 1)
    points[:, 0] *= width - 1
    points[:, 1] *= height - 1
    return np.rint(points).astype(np.int32)
