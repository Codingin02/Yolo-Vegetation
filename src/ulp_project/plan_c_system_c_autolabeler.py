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
