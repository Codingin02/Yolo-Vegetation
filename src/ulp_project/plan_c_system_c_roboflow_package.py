"""Roboflow review package builder for System C final."""

from __future__ import annotations

import csv
from pathlib import Path
import shutil
from typing import Any

from .paths import PROJECT_ROOT
from .plan_c_system_c_yolo_exporter import CLASS_NAMES, write_class_files

DATASET_FINAL_ROOT = PROJECT_ROOT / "data" / "dataset_yolo" / "plan_c_final_v1"
ROBOFLOW_ROOT = DATASET_FINAL_ROOT / "roboflow_package"


def build_roboflow_package(rows: list[dict[str, Any]] | None = None, *, dataset_root: Path = DATASET_FINAL_ROOT) -> dict[str, Any]:
    write_class_files(dataset_root)
    package_root = dataset_root / "roboflow_package"
    if package_root.exists():
        shutil.rmtree(package_root)
    images_dir = package_root / "images"
    labels_dir = package_root / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    copied_images = 0
    copied_labels = 0
    for row in rows or []:
        local_path = Path(str(row.get("dataset_image_path") or row.get("local_path") or ""))
        if local_path.exists() and local_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            shutil.copy2(local_path, images_dir / local_path.name)
            copied_images += 1
            label_path = Path(str(row.get("dataset_label_path") or "")) if row.get("dataset_label_path") else local_path.with_suffix(".txt")
            if label_path.exists():
                shutil.copy2(label_path, labels_dir / label_path.name)
                copied_labels += 1
    _write_readme(package_root / "README_ROBOFLOW_IMPORT.md")
    _write_csv(package_root / "manifest.csv", rows or [])
    _write_csv(package_root / "source_attribution.csv", rows or [])
    _write_csv(package_root / "license_manifest.csv", rows or [])
    _write_csv(package_root / "rejected_report.csv", [row for row in rows or [] if str(row.get("accepted_status", "")).startswith("REJECT")])
    return {
        "status": "ROBOFLOW_REVIEW_PACKAGE_READY" if copied_images > 0 and copied_labels > 0 else "ROBOFLOW_REVIEW_PACKAGE_NOT_READY",
        "package_dir": str(package_root),
        "copied_images": copied_images,
        "copied_label_files": copied_labels,
        "classes": CLASS_NAMES,
    }


def _write_readme(path: Path) -> None:
    path.write_text(
        "Plan C System C Roboflow review package.\n"
        "Review all boxes manually before training. Negative images may have no label file.\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row.keys()} or {"status"})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
