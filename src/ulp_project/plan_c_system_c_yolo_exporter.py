"""YOLO dataset export helpers for System C final."""

from __future__ import annotations

import csv
from pathlib import Path
import random
import shutil
from typing import Any

from .paths import PROJECT_ROOT
from .plan_c_system_c_autolabeler import validate_yolo_line

DATASET_FINAL_ROOT = PROJECT_ROOT / "data" / "dataset_yolo" / "plan_c_final_v1"
CLASS_NAMES = ["struktur_penyangga", "konduktor", "pohon_sono", "pohon_non_sono"]
SPLIT_SEED = 23050874166


def write_class_files(dataset_root: Path = DATASET_FINAL_ROOT) -> None:
    dataset_root.mkdir(parents=True, exist_ok=True)
    (dataset_root / "classes.txt").write_text("\n".join(CLASS_NAMES) + "\n", encoding="utf-8")
    (dataset_root / "data.yaml").write_text(
        "path: E:/Projects/ULP_Project/data/dataset_yolo/plan_c_final_v1\n"
        "train: images/train\nval: images/val\ntest: images/test\n\nnames:\n"
        "  0: struktur_penyangga\n  1: konduktor\n  2: pohon_sono\n  3: pohon_non_sono\n",
        encoding="utf-8",
    )


def validate_label_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "LABEL_MISSING", "valid": False, "class_counts": {}}
    class_counts: dict[str, int] = {}
    valid = True
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        if not validate_yolo_line(line):
            valid = False
            continue
        class_id = line.split()[0]
        class_counts[class_id] = class_counts.get(class_id, 0) + 1
    return {"status": "LABEL_VALID" if valid else "LABEL_INVALID", "valid": valid, "class_counts": class_counts}


def build_review_split(rows: list[dict[str, Any]], *, dataset_root: Path = DATASET_FINAL_ROOT) -> dict[str, Any]:
    write_class_files(dataset_root)
    usable = [row for row in rows if row.get("local_path") and Path(str(row["local_path"])).exists()]
    random.Random(SPLIT_SEED).shuffle(usable)
    counts = {"train": 0, "val": 0, "test": 0}
    for index, row in enumerate(usable):
        split = "test" if index % 10 == 0 else "val" if index % 5 == 0 else "train"
        image_path = Path(str(row["local_path"]))
        target_image = dataset_root / "images" / split / image_path.name
        target_image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, target_image)
        counts[split] += 1
    return {"status": "YOLO_REVIEW_SPLIT_CREATED", "counts": counts, "image_count": len(usable)}


def read_manifest_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]
