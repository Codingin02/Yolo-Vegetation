"""YOLO dataset export helpers for System C final."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import random
import shutil
from typing import Any

from .paths import PROJECT_ROOT
from .plan_c_system_c_autolabeler import autolabel_review_image, validate_yolo_line
from .plan_c_system_c_image_quality import inspect_image

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
    _clear_managed_export(dataset_root)
    usable = [
        row
        for row in rows
        if row.get("local_path")
        and Path(str(row["local_path"])).exists()
        and str(row.get("accepted_status") or row.get("status") or "").startswith("ACCEPT")
    ]
    usable = _dedupe_rows_by_image(usable)
    random.Random(SPLIT_SEED).shuffle(usable)
    counts = {"train": 0, "val": 0, "test": 0}
    label_count = 0
    needs_manual = 0
    exported_rows: list[dict[str, Any]] = []
    for index, row in enumerate(usable):
        split = "test" if index % 10 == 0 else "val" if index % 5 == 0 else "train"
        image_path = Path(str(row["local_path"]))
        quality = inspect_image(image_path)
        if not quality.get("quality_pass"):
            exported_rows.append(
                {
                    **row,
                    "accepted_status": quality.get("status") or "REJECT_LOW_QUALITY",
                    "review_status": "rejected_pseudo_label",
                    "label_status": "NO_LABEL_IMAGE_QUALITY_FAILED",
                    "quality_status": quality.get("status"),
                    "width": quality.get("width", ""),
                    "height": quality.get("height", ""),
                    "not_ground_truth": True,
                }
            )
            continue
        target_class = _target_class(row)
        target_image = dataset_root / "images" / split / _dataset_filename(row, image_path, target_class)
        target_image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, target_image)
        counts[split] += 1
        label_path = dataset_root / "labels" / split / f"{target_image.stem}.txt"
        label_result = autolabel_review_image(target_image, target_class=target_class, label_path=label_path)
        row_update = {
            **row,
            "dataset_image_path": str(target_image),
            "dataset_label_path": str(label_path) if label_path.exists() else "",
            "review_status": "needs_manual_check",
            "label_status": label_result.get("status"),
            "label_written": bool(label_result.get("label_written")),
            "quality_status": quality.get("status"),
            "width": quality.get("width", ""),
            "height": quality.get("height", ""),
            "not_ground_truth": True,
        }
        if label_result.get("label_written"):
            label_count += 1
            _copy_review_artifacts(dataset_root / "review" / "accepted_pseudo_label", target_image, label_path)
        else:
            needs_manual += 1
            _copy_review_artifacts(dataset_root / "review" / "needs_manual_check", target_image, None)
        exported_rows.append(row_update)
    return {
        "status": "YOLO_REVIEW_SPLIT_CREATED",
        "counts": counts,
        "image_count": sum(counts.values()),
        "label_count": label_count,
        "needs_manual_check_count": needs_manual,
        "rows": exported_rows,
    }


def read_manifest_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _target_class(row: dict[str, Any]) -> str:
    target = str(row.get("target_class") or "non_target").strip()
    return target if target in {"struktur_penyangga", "konduktor", "pohon_sono", "pohon_non_sono", "non_target"} else "non_target"


def _dataset_filename(row: dict[str, Any], image_path: Path, target_class: str) -> str:
    digest_source = str(row.get("sha256") or row.get("image_url") or image_path.name)
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:12]
    suffix = image_path.suffix.lower() if image_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
    return f"{target_class}_{digest}{suffix}"


def _copy_review_artifacts(review_dir: Path, image_path: Path, label_path: Path | None) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_path, review_dir / image_path.name)
    if label_path and label_path.exists():
        shutil.copy2(label_path, review_dir / label_path.name)


def _dedupe_rows_by_image(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = str(row.get("sha256") or row.get("image_url") or row.get("local_path") or "")
        if not key:
            key = str(row)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def _clear_managed_export(dataset_root: Path) -> None:
    prefixes = tuple(f"{name}_" for name in [*CLASS_NAMES, "non_target"])
    for base in [dataset_root / "images", dataset_root / "labels"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.name.startswith(prefixes):
                path.unlink()
    for review_name in ["needs_manual_check", "accepted_pseudo_label", "rejected_pseudo_label"]:
        review_dir = dataset_root / "review" / review_name
        if review_dir.exists():
            shutil.rmtree(review_dir)
