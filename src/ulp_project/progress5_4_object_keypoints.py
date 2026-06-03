"""BBox keypoint extraction for pole, conductor, and tree canopy."""

from __future__ import annotations

from typing import Any


POLE_CLASS = "struktur_penyangga"
CONDUCTOR_CLASS = "konduktor"
TREE_CLASS = "pohon_sono"


def extract_object_keypoints(detections: list[dict[str, Any]]) -> dict[str, Any]:
    pole = _best_detection(detections, POLE_CLASS)
    conductor = _best_detection(detections, CONDUCTOR_CLASS)
    tree = _best_detection(detections, TREE_CLASS)
    result = {
        "status": "OBJECT_KEYPOINTS_READY",
        "pole_detected": pole is not None,
        "conductor_detected": conductor is not None,
        "tree_detected": tree is not None,
        "pole_bbox": _bbox(pole),
        "conductor_bbox": _bbox(conductor),
        "tree_bbox": _bbox(tree),
        "detected_classes": sorted({str(item.get("class_name") or "") for item in detections if item.get("class_name")}),
    }
    if pole:
        bbox = _bbox(pole)
        result.update(
            {
                "pole_top_px": bbox[1],
                "pole_base_px": bbox[3],
                "pole_pixel_height": max(bbox[3] - bbox[1], 0.0),
            }
        )
    if conductor:
        bbox = _bbox(conductor)
        result.update(
            {
                "cable_px": (bbox[1] + bbox[3]) / 2.0,
                "cable_lowest_px": bbox[3],
                "cable_centerline_px": (bbox[1] + bbox[3]) / 2.0,
            }
        )
    if tree:
        bbox = _bbox(tree)
        result.update(
            {
                "tree_top_px": bbox[1],
                "tree_bottom_px": bbox[3],
                "tree_pixel_height": max(bbox[3] - bbox[1], 0.0),
            }
        )
    return result


def _best_detection(detections: list[dict[str, Any]], class_name: str) -> dict[str, Any] | None:
    matches = [item for item in detections if str(item.get("class_name") or item.get("label") or "") == class_name]
    if not matches:
        return None
    return max(matches, key=lambda item: float(item.get("confidence") or 0.0))


def _bbox(item: dict[str, Any] | None) -> list[float] | None:
    if item is None:
        return None
    values = item.get("bbox_xyxy") or item.get("bbox") or []
    if len(values) != 4:
        return None
    return [float(value) for value in values]
