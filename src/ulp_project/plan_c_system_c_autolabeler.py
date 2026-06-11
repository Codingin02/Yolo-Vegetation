"""Review-only YOLO-compatible pre-label helpers for System C."""

from __future__ import annotations

from pathlib import Path
from typing import Any

CLASS_TO_ID = {
    "struktur_penyangga": 0,
    "konduktor": 1,
    "pohon_sono": 2,
    "pohon_non_sono": 3,
}


def validate_yolo_line(line: str) -> bool:
    parts = line.strip().split()
    if len(parts) != 5:
        return False
    try:
        class_id = int(parts[0])
        values = [float(value) for value in parts[1:]]
    except ValueError:
        return False
    return class_id in {0, 1, 2, 3} and all(0.0 <= value <= 1.0 for value in values)


def write_review_label(label_path: Path, *, target_class: str, bbox: list[float] | None = None) -> dict[str, Any]:
    label_path.parent.mkdir(parents=True, exist_ok=True)
    if target_class == "non_target" or bbox is None:
        return {
            "status": "PSEUDO_LABEL_REVIEW_REQUIRED_NO_AUTO_BBOX",
            "label_written": False,
            "needs_manual_check": True,
            "not_ground_truth": True,
        }
    class_id = CLASS_TO_ID.get(target_class)
    if class_id is None or len(bbox) != 4 or not all(0.0 <= float(value) <= 1.0 for value in bbox):
        return {
            "status": "PSEUDO_LABEL_INVALID_INPUT_NEEDS_MANUAL_CHECK",
            "label_written": False,
            "needs_manual_check": True,
            "not_ground_truth": True,
        }
    line = f"{class_id} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}"
    label_path.write_text(line + "\n", encoding="utf-8")
    return {
        "status": "PSEUDO_LABEL_REVIEW_REQUIRED",
        "label_written": True,
        "needs_manual_check": True,
        "not_ground_truth": True,
    }


def autolabel_review_image(image_path: Path, *, target_class: str, label_path: Path) -> dict[str, Any]:
    """Create a conservative review-only YOLO label when image evidence is enough.

    This is deliberately limited. It uses visible vegetation color segmentation
    only for tree classes and refuses to invent conductor/structure boxes.
    """

    target_class = str(target_class or "").strip()
    if target_class == "non_target":
        return {
            "status": "NEGATIVE_SAMPLE_NO_LABEL",
            "label_written": False,
            "needs_manual_check": False,
            "not_ground_truth": True,
            "reason": "Negative sample: no target bbox created.",
        }
    if target_class not in {"pohon_sono", "pohon_non_sono"}:
        return {
            "status": "PSEUDO_LABEL_ENGINE_NOT_CONFIDENT_NEEDS_MANUAL_CHECK",
            "label_written": False,
            "needs_manual_check": True,
            "not_ground_truth": True,
            "reason": "No reliable local detector for conductor/structure in dataset pipeline.",
        }
    bbox = _vegetation_bbox_xywh_normalized(image_path)
    if bbox is None:
        return {
            "status": "PSEUDO_LABEL_ENGINE_NOT_CONFIDENT_NEEDS_MANUAL_CHECK",
            "label_written": False,
            "needs_manual_check": True,
            "not_ground_truth": True,
            "reason": "Vegetation segmentation not confident enough for a review-only bbox.",
        }
    result = write_review_label(label_path, target_class=target_class, bbox=bbox)
    return {
        **result,
        "reason": "Conservative vegetation color segmentation; manual review required.",
        "bbox_xywh_normalized": bbox,
    }


def _vegetation_bbox_xywh_normalized(image_path: Path) -> list[float] | None:
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception:
        return None
    width, height = image.size
    if width < 120 or height < 120:
        return None
    step = max(1, int(max(width, height) / 480))
    xs: list[int] = []
    ys: list[int] = []
    sample_count = 0
    for y in range(0, height, step):
        for x in range(0, width, step):
            r, g, b = image.getpixel((x, y))
            sample_count += 1
            is_green = g > 60 and g > r * 1.08 and g > b * 1.03
            is_brown = r > 65 and g > 35 and b < 120 and r >= g >= b * 0.6
            if is_green or is_brown:
                xs.append(x)
                ys.append(y)
    if not xs or not ys or sample_count <= 0:
        return None
    mask_fraction = len(xs) / sample_count
    if mask_fraction < 0.035:
        return None
    sorted_xs = sorted(xs)
    sorted_ys = sorted(ys)
    low_index = max(0, int(len(sorted_xs) * 0.02))
    high_index = min(len(sorted_xs) - 1, int(len(sorted_xs) * 0.98))
    x1 = max(sorted_xs[low_index] - step * 2, 0)
    x2 = min(sorted_xs[high_index] + step * 2, width)
    y1 = max(sorted_ys[low_index] - step * 2, 0)
    y2 = min(sorted_ys[high_index] + step * 2, height)
    box_w = x2 - x1
    box_h = y2 - y1
    area_fraction = (box_w * box_h) / float(width * height)
    if box_w < width * 0.12 or box_h < height * 0.12:
        return None
    if area_fraction > 0.94:
        return None
    x_center = (x1 + x2) / 2.0 / width
    y_center = (y1 + y2) / 2.0 / height
    norm_w = box_w / width
    norm_h = box_h / height
    bbox = [x_center, y_center, norm_w, norm_h]
    return [round(max(0.0, min(float(value), 1.0)), 6) for value in bbox]
