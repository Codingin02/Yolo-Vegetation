"""Build YOLOv8 review-only packages for Plan C priority acquisition."""

from __future__ import annotations

import csv
from datetime import datetime
import random
import shutil
from pathlib import Path
from typing import Any

from .plan_c_priority_acquisition_config import CLASS_MAPPING, YOLOV8_REVIEW_PACKAGE_ROOT, ensure_priority_acquisition_dirs
from .plan_c_priority_pseudo_labeler import empty_label_for_manual_review
from .plan_c_priority_source_manifest import accepted_for_packaging, latest_manifest_rows

SPLIT_SEED = 23050874166


def build_yolov8_priority_review_package(
    *,
    mode: str = "dry-run",
    rows: list[dict[str, Any]] | None = None,
    output_root: Path | None = None,
    val_ratio: float = 0.2,
) -> dict[str, Any]:
    ensure_priority_acquisition_dirs()
    rows = accepted_for_packaging(rows if rows is not None else latest_manifest_rows())
    local_rows = [row for row in rows if row.get("local_path") and Path(str(row.get("local_path"))).exists()]
    if mode == "dry-run":
        return {
            "ok": True,
            "status": "YOLOV8_PRIORITY_REVIEW_PACKAGE_DRY_RUN_READY",
            "accepted_manifest_rows": len(rows),
            "local_images_available": len(local_rows),
            "not_final_training_dataset": True,
        }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = (output_root or YOLOV8_REVIEW_PACKAGE_ROOT) / f"plan_c_priority_yolov8_review_{timestamp}"
    for sub in ["images/train", "images/val", "labels/train", "labels/val"]:
        (root / sub).mkdir(parents=True, exist_ok=True)

    shuffled = list(local_rows)
    random.Random(SPLIT_SEED).shuffle(shuffled)
    val_count = max(1 if len(shuffled) > 1 else 0, int(round(len(shuffled) * val_ratio)))
    val_ids = {id(row) for row in shuffled[:val_count]}
    package_rows: list[dict[str, Any]] = []

    for index, row in enumerate(shuffled):
        split = "val" if id(row) in val_ids else "train"
        source_path = Path(str(row["local_path"]))
        image_name = f"{index:05d}_{source_path.name}"
        image_path = root / "images" / split / image_name
        label_path = root / "labels" / split / (Path(image_name).stem + ".txt")
        shutil.copy2(source_path, image_path)
        empty_label_for_manual_review(label_path)
        package_row = dict(row)
        package_row["split"] = split
        package_row["package_image"] = str(image_path)
        package_row["package_label"] = str(label_path)
        package_row["review_only"] = "true"
        package_rows.append(package_row)

    _write_manifest(root / "manifest.csv", package_rows)
    _write_data_yaml(root / "data.yaml")
    _write_readme(root / "README_REVIEW_ONLY.md")
    return {
        "ok": True,
        "status": "YOLOV8_PRIORITY_REVIEW_PACKAGE_CREATED_NOT_FINAL_DATASET",
        "package_root": str(root),
        "image_count": len(package_rows),
        "split_seed": SPLIT_SEED,
        "not_final_training_dataset": True,
    }


def _write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row.keys()} | {"review_only", "split"})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_data_yaml(path: Path) -> None:
    lines = ["path: .", "train: images/train", "val: images/val", "names:"]
    lines.extend(f"  {index}: {name}" for index, name in CLASS_MAPPING.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_readme(path: Path) -> None:
    path.write_text(
        """# Plan C YOLOv8 Review Package

Status: YOLOV8_PRIORITY_REVIEW_PACKAGE_CREATED_NOT_FINAL_DATASET.

This package is review-only. Empty labels mean the image must be manually reviewed before training. Do not train until Roboflow/manual review validates bounding boxes and class mapping.
""",
        encoding="utf-8",
    )
