from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "data" / "dataset_yolo"
METADATA_DIR = ROOT / "data" / "metadata"

FINAL_CLASS_IDS = {
    "struktur_penyangga": 0,
    "konduktor": 1,
    "pohon_sono": 2,
    "pohon_non_sono": 3,
}
REQUIRED_CLASSES = ["struktur_penyangga", "konduktor", "pohon_sono"]


def main() -> int:
    args = parse_args()
    audit_path = Path(args.audit) if args.audit else _latest_audit_path()
    if not audit_path or not audit_path.exists():
        raise SystemExit("PLAN_C_DATASET_AUDIT_NOT_FOUND")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if not audit.get("ready_for_training"):
        summary = {
            "status": "DATASET_NOT_READY",
            "audit_path": str(audit_path),
            "shortfalls": audit.get("shortfalls", {}),
            "dataset_created": False,
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    output_dir = _next_output_dir(args.output)
    class_names = _selected_class_names(audit)
    output_dir.mkdir(parents=True, exist_ok=False)
    for split in ("train", "val", "test"):
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, Any]] = []
    split_counts: dict[str, int] = {"train": 0, "val": 0, "test": 0}
    class_counts: dict[str, int] = {name: 0 for name in class_names.values()}
    copied_images: set[str] = set()

    records = audit.get("valid_records") or []
    for index, record in enumerate(records):
        image_path = Path(record.get("image_path", ""))
        if not image_path.exists():
            continue
        valid_lines = _normalize_lines(record.get("valid_lines"), class_names)
        if not valid_lines:
            continue
        image_hash = _stable_hash(str(image_path.resolve()))
        dest_stem = f"{index + 1:06d}_{image_path.stem}_{image_hash[:10]}"
        split = _split_for_hash(image_hash)
        dest_image = output_dir / "images" / split / f"{dest_stem}{image_path.suffix.lower()}"
        dest_label = output_dir / "labels" / split / f"{dest_stem}.txt"
        shutil.copy2(image_path, dest_image)
        dest_label.write_text("\n".join(valid_lines) + "\n", encoding="utf-8")
        copied_images.add(str(dest_image))
        split_counts[split] += 1
        row_counts = _class_counts_from_lines(valid_lines, class_names)
        for name, count in row_counts.items():
            class_counts[name] = class_counts.get(name, 0) + count
        manifest_rows.append(
            {
                "dataset_image": str(dest_image),
                "dataset_label": str(dest_label),
                "source_image": str(image_path),
                "source_label": str(record.get("label_path", "")),
                "source_root": str(record.get("source_root", "")),
                "split": split,
                "class_counts": json.dumps(row_counts, sort_keys=True),
                "status": "COPIED_VALID_YOLO_LABEL",
            }
        )

    _write_data_yaml(output_dir, class_names)
    _write_class_mapping(output_dir, class_names)
    _write_manifest(output_dir, manifest_rows)
    dataset_audit = {
        "status": "PLAN_C_SYSTEM_C_DATASET_READY",
        "source_audit_path": str(audit_path),
        "dataset_path": str(output_dir),
        "image_count": len(copied_images),
        "label_file_count": len(manifest_rows),
        "split_counts": split_counts,
        "class_counts": class_counts,
        "class_names": class_names,
        "source_data_modified": False,
    }
    (output_dir / "dataset_audit.json").write_text(json.dumps(dataset_audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(dataset_audit, indent=2, ensure_ascii=False))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build final Plan C System C YOLOv8 dataset from audited labels.")
    parser.add_argument("--audit", default="", help="Path to plan_c_training_dataset_audit_*.json")
    parser.add_argument("--output", default="", help="Optional output dataset directory")
    return parser.parse_args()


def _latest_audit_path() -> Path | None:
    candidates = sorted(METADATA_DIR.glob("plan_c_training_dataset_audit_*.json"))
    return candidates[-1] if candidates else None


def _next_output_dir(value: str) -> Path:
    if value:
        path = Path(value)
        return path if path.is_absolute() else ROOT / path
    base = DATASET_ROOT / "plan_c_system_c_detector_v2"
    if not base.exists():
        return base
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DATASET_ROOT / f"plan_c_system_c_detector_v2_{timestamp}"


def _selected_class_names(audit: dict[str, Any]) -> dict[int, str]:
    recommended = set(audit.get("recommended_classes") or [])
    names = {FINAL_CLASS_IDS[name]: name for name in REQUIRED_CLASSES}
    if "pohon_non_sono" in recommended:
        names[3] = "pohon_non_sono"
    return dict(sorted(names.items()))


def _normalize_lines(raw_lines: Any, class_names: dict[int, str]) -> list[str]:
    if not isinstance(raw_lines, list):
        return []
    allowed_names = set(class_names.values())
    normalized: list[str] = []
    for line in raw_lines:
        if not isinstance(line, dict):
            continue
        class_name = str(line.get("class_name") or "")
        if class_name not in allowed_names:
            continue
        try:
            class_id = FINAL_CLASS_IDS[class_name]
            x, y, w, h = [float(line[key]) for key in ("x", "y", "w", "h")]
        except (KeyError, TypeError, ValueError):
            continue
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
            continue
        normalized.append(f"{class_id} {x:.8f} {y:.8f} {w:.8f} {h:.8f}")
    return normalized


def _split_for_hash(value: str) -> str:
    bucket = int(value[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 95:
        return "val"
    return "test"


def _stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _class_counts_from_lines(lines: list[str], class_names: dict[int, str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        class_id = int(line.split()[0])
        name = class_names.get(class_id, f"class_{class_id}")
        counts[name] = counts.get(name, 0) + 1
    return counts


def _write_data_yaml(output_dir: Path, class_names: dict[int, str]) -> None:
    names_block = "\n".join(f"  {class_id}: {name}" for class_id, name in class_names.items())
    text = (
        f"path: {output_dir.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        "names:\n"
        f"{names_block}\n"
    )
    (output_dir / "data.yaml").write_text(text, encoding="utf-8")


def _write_class_mapping(output_dir: Path, class_names: dict[int, str]) -> None:
    mapping = {
        "class_policy": "system_c_tree_conductor_structure",
        "names": {str(class_id): name for class_id, name in class_names.items()},
    }
    (output_dir / "class_mapping.json").write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_manifest(output_dir: Path, rows: list[dict[str, Any]]) -> None:
    path = output_dir / "dataset_manifest.csv"
    fieldnames = ["dataset_image", "dataset_label", "source_image", "source_label", "source_root", "split", "class_counts", "status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
