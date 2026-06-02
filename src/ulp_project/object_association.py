"""Lightweight object association for frame-to-frame detections."""

from __future__ import annotations

from math import hypot
from typing import Any

from .vision_geometry import bbox_center


def iou(a: list[float], b: list[float]) -> float:
    x1 = max(float(a[0]), float(b[0]))
    y1 = max(float(a[1]), float(b[1]))
    x2 = min(float(a[2]), float(b[2]))
    y2 = min(float(a[3]), float(b[3]))
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, float(a[2]) - float(a[0])) * max(0.0, float(a[3]) - float(a[1]))
    area_b = max(0.0, float(b[2]) - float(b[0])) * max(0.0, float(b[3]) - float(b[1]))
    denom = area_a + area_b - inter
    return 0.0 if denom <= 0 else inter / denom


def centroid_distance(a: list[float], b: list[float]) -> float:
    ax, ay = bbox_center(a)
    bx, by = bbox_center(b)
    return hypot(ax - bx, ay - by)


def associate_detections(previous: list[dict[str, Any]], current: list[dict[str, Any]], iou_threshold: float = 0.2) -> list[dict[str, Any]]:
    associated: list[dict[str, Any]] = []
    used: set[int] = set()
    for item in current:
        best_idx = None
        best_iou = 0.0
        for idx, prev in enumerate(previous):
            if idx in used:
                continue
            score = iou(prev.get("bbox", [0, 0, 0, 0]), item.get("bbox", [0, 0, 0, 0]))
            if score > best_iou:
                best_iou = score
                best_idx = idx
        next_item = dict(item)
        if best_idx is not None and best_iou >= iou_threshold:
            used.add(best_idx)
            next_item["track_id"] = previous[best_idx].get("track_id", f"track_{best_idx}")
            next_item["association_status"] = "MATCHED_IOU"
            next_item["association_iou"] = round(best_iou, 3)
        else:
            next_item["track_id"] = f"new_{len(associated)}"
            next_item["association_status"] = "NEW_TRACK"
            next_item["association_iou"] = 0.0
        associated.append(next_item)
    return associated
