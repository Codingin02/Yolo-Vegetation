"""Training gate for System C final YOLO dataset."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .plan_c_system_c_yolo_exporter import CLASS_NAMES, validate_label_file

DATASET_ROOT = PROJECT_ROOT / "data" / "dataset_yolo" / "plan_c_final_v1"
THRESHOLDS = {
    "pohon_sono": 80,
    "konduktor": 60,
    "struktur_penyangga": 40,
    "pohon_non_sono": 40,
    "non_target_negative": 60,
}


def run_training_gate(dataset_root: Path = DATASET_ROOT) -> dict[str, Any]:
    image_counts = _count_images(dataset_root)
    label_counts = _count_labels(dataset_root)
    class_label_counts = _class_label_counts(dataset_root)
    duplicate_count = _duplicate_image_count(dataset_root)
    class_ready = {
        "pohon_sono": image_counts.get("pohon_sono", 0) >= THRESHOLDS["pohon_sono"] and class_label_counts.get("2", 0) >= THRESHOLDS["pohon_sono"],
        "konduktor": image_counts.get("konduktor", 0) >= THRESHOLDS["konduktor"] and class_label_counts.get("1", 0) >= THRESHOLDS["konduktor"],
        "struktur_penyangga": image_counts.get("struktur_penyangga", 0) >= THRESHOLDS["struktur_penyangga"] and class_label_counts.get("0", 0) >= THRESHOLDS["struktur_penyangga"],
        "pohon_non_sono": image_counts.get("pohon_non_sono", 0) >= THRESHOLDS["pohon_non_sono"],
        "non_target_negative": image_counts.get("non_target", 0) >= THRESHOLDS["non_target_negative"],
    }
    yaml_ok = (dataset_root / "data.yaml").exists()
    classes_ok = (dataset_root / "classes.txt").exists()
    ready = all(class_ready.values()) and yaml_ok and classes_ok and duplicate_count == 0
    return {
        "status": "YOLO_TRAINING_READY" if ready else "YOLO_TRAINING_SKIPPED_DATASET_NOT_READY",
        "dataset_root": str(dataset_root),
        "thresholds": THRESHOLDS,
        "image_counts": image_counts,
        "label_files": label_counts,
        "class_label_counts": class_label_counts,
        "class_ready": class_ready,
        "data_yaml_exists": yaml_ok,
        "classes_txt_exists": classes_ok,
        "duplicate_image_hash_count": duplicate_count,
        "training_allowed": ready,
        "classes": CLASS_NAMES,
    }


def _count_images(root: Path) -> dict[str, int]:
    counts = {"pohon_sono": 0, "konduktor": 0, "struktur_penyangga": 0, "pohon_non_sono": 0, "non_target": 0, "total": 0}
    for path in (root / "images").rglob("*") if (root / "images").exists() else []:
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        counts["total"] += 1
        lowered = str(path).lower()
        matched = False
        for key in ["pohon_sono", "konduktor", "struktur_penyangga", "pohon_non_sono"]:
            if key in lowered:
                counts[key] += 1
                matched = True
                break
        if not matched:
            counts["non_target"] += 1
    return counts


def _count_labels(root: Path) -> dict[str, int]:
    files = list((root / "labels").rglob("*.txt")) if (root / "labels").exists() else []
    valid = sum(1 for path in files if validate_label_file(path).get("valid"))
    return {"total": len(files), "valid": valid, "invalid": len(files) - valid}


def _class_label_counts(root: Path) -> dict[str, int]:
    counts = {"0": 0, "1": 0, "2": 0, "3": 0}
    for path in (root / "labels").rglob("*.txt") if (root / "labels").exists() else []:
        result = validate_label_file(path)
        for class_id, value in result.get("class_counts", {}).items():
            if class_id in counts:
                counts[class_id] += int(value)
    return counts


def _duplicate_image_count(root: Path) -> int:
    seen: set[str] = set()
    duplicates = 0
    for path in (root / "images").rglob("*") if (root / "images").exists() else []:
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        digest = _sha256(path)
        if digest in seen:
            duplicates += 1
        seen.add(digest)
    return duplicates


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
