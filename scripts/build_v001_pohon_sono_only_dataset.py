from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.yolo_label_audit import IMAGE_EXTENSIONS, read_yolo_label_file  # noqa: E402

PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
SOURCE_IMAGE_DIR = PROJECT_ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "images_selected"
SOURCE_LABEL_DIR = PROJECT_ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "labels_selected"
OUTPUT_DIR = PROJECT_ROOT / "data" / "dataset_yolo" / "v001_pohon_sono_only_v1"
SEED = 23050874166
ORIGINAL_TREE_CLASS = 2
NEW_TREE_CLASS = 0


def collect_items() -> list[dict]:
    images = sorted(path for path in SOURCE_IMAGE_DIR.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    labels = {path.stem: path for path in SOURCE_LABEL_DIR.glob("*.txt") if path.is_file()}
    items = []
    for image in images:
        label = labels.get(image.stem)
        parsed = read_yolo_label_file(label) if label else {"status": "MISSING", "errors": [{"code": "MISSING_LABEL"}], "boxes": []}
        kept_rows = []
        dropped_counts: dict[int, int] = {}
        for box in parsed.get("boxes", []):
            class_id = int(box["class_id"])
            if class_id == ORIGINAL_TREE_CLASS:
                kept_rows.append(
                    f"{NEW_TREE_CLASS} {box['x_center']:.12g} {box['y_center']:.12g} {box['width']:.12g} {box['height']:.12g}"
                )
            else:
                dropped_counts[class_id] = dropped_counts.get(class_id, 0) + 1
        items.append(
            {
                "image": image,
                "label": label,
                "source_status": parsed["status"],
                "kept_rows": kept_rows,
                "dropped_counts": dropped_counts,
                "errors": parsed.get("errors", []),
            }
        )
    return items


def split_items(items: list[dict], val_ratio: float = 0.2, seed: int = SEED) -> dict[str, list[dict]]:
    shuffled = list(items)
    random.Random(seed).shuffle(shuffled)
    val_count = max(1, round(len(shuffled) * val_ratio)) if len(shuffled) > 1 else 0
    val = shuffled[:val_count]
    train = shuffled[val_count:]
    return {"train": train, "val": val}


def build_dataset(splits: dict[str, list[dict]]) -> None:
    if OUTPUT_DIR.resolve() == (PROJECT_ROOT / "data" / "dataset_yolo" / "field_multiclass_v1").resolve():
        raise RuntimeError("Refusing to overwrite field_multiclass_v1")
    for split_name, items in splits.items():
        for item in items:
            image_target = OUTPUT_DIR / "images" / split_name / item["image"].name
            label_target = OUTPUT_DIR / "labels" / split_name / f"{item['image'].stem}.txt"
            image_target.parent.mkdir(parents=True, exist_ok=True)
            label_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item["image"], image_target)
            label_target.write_text("\n".join(item["kept_rows"]) + ("\n" if item["kept_rows"] else ""), encoding="utf-8")
    write_data_yaml()
    write_manifest(splits)
    write_report(splits, "DATASET_BUILD_READY")


def write_data_yaml() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"path: {OUTPUT_DIR.as_posix()}",
        "train: images/train",
        "val: images/val",
        "names:",
        "  0: pohon_sono",
    ]
    path = OUTPUT_DIR / "data.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_manifest(splits: dict[str, list[dict]]) -> None:
    path = OUTPUT_DIR / "dataset_manifest.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["split", "image", "source_label", "pohon_sono_boxes", "dropped_non_tree_boxes"])
        for split_name, items in splits.items():
            for item in items:
                writer.writerow(
                    [
                        split_name,
                        item["image"].name,
                        item["label"].name if item["label"] else "",
                        len(item["kept_rows"]),
                        sum(item["dropped_counts"].values()),
                    ]
                )


def write_report(splits: dict[str, list[dict]], status: str) -> Path:
    path = OUTPUT_DIR / "dataset_build_report.json"
    path.write_text(json.dumps(summarize(splits, status), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def summarize(splits: dict[str, list[dict]], status: str) -> dict:
    all_items = [item for items in splits.values() for item in items]
    kept = sum(len(item["kept_rows"]) for item in all_items)
    dropped: dict[int, int] = {}
    for item in all_items:
        for class_id, count in item["dropped_counts"].items():
            dropped[class_id] = dropped.get(class_id, 0) + count
    missing = [item["image"].name for item in all_items if item["label"] is None]
    errors = [item["image"].name for item in all_items if item["errors"]]
    empty_after_filter = [item["image"].name for item in all_items if not item["kept_rows"]]
    return {
        "status": status,
        "source_images": str(SOURCE_IMAGE_DIR),
        "source_labels": str(SOURCE_LABEL_DIR),
        "output_dir": str(OUTPUT_DIR),
        "seed": SEED,
        "val_ratio": 0.2,
        "total_images": len(all_items),
        "train_images": len(splits["train"]),
        "val_images": len(splits["val"]),
        "class_distribution": {"pohon_sono": kept},
        "dropped_original_class_counts": {
            "struktur_penyangga": dropped.get(0, 0),
            "konduktor": dropped.get(1, 0),
        },
        "missing_source_labels": missing,
        "source_label_errors": errors,
        "empty_labels_after_filter": empty_after_filter,
        "data_yaml": str(OUTPUT_DIR / "data.yaml"),
        "no_raw_data_modified": True,
        "no_field_multiclass_overwrite": True,
        "no_fake_label": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V001 pohon_sono-only YOLO dataset from selected manual labels.")
    parser.add_argument("--mode", choices=["dry-run", "build"], default="dry-run")
    args = parser.parse_args()
    items = collect_items()
    splits = split_items(items)
    summary = summarize(splits, "DATASET_BUILD_DRY_RUN_READY" if args.mode == "dry-run" else "DATASET_BUILD_READY")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if summary["missing_source_labels"] or summary["source_label_errors"]:
        print("result: SOURCE_LABELS_NOT_READY")
        return 1
    if summary["class_distribution"]["pohon_sono"] <= 0:
        print("result: NO_POHON_SONO_LABELS")
        return 1
    if args.mode == "build":
        build_dataset(splits)
        print("result: DATASET_BUILD_READY")
    else:
        print("result: DATASET_BUILD_DRY_RUN_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
