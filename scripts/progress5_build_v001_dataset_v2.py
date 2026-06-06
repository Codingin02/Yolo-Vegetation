from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from progress5_audit_v001_labels import audit_v001_labels, resolve_path as resolve_project_path  # noqa: E402


SAFE_SEED = 1576037691
DEFAULT_IMAGE_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "images_selected"
DEFAULT_LABEL_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "labels_selected"
DEFAULT_DATASET_DIR = ROOT / "data" / "dataset_yolo" / "v001_pohon_sono_only_v2"
DEFAULT_SUMMARY_PATH = ROOT / "data" / "metadata" / "progress5_v001_dataset_v2_build_summary.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def list_image_label_pairs(image_dir: Path, label_dir: Path) -> list[tuple[Path, Path]]:
    images = sorted(path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    pairs: list[tuple[Path, Path]] = []
    for image_path in images:
        label_path = label_dir / f"{image_path.stem}.txt"
        if label_path.exists():
            pairs.append((image_path, label_path))
    return pairs


def split_pairs(pairs: list[tuple[Path, Path]], seed: int = SAFE_SEED, val_ratio: float = 0.2) -> dict[str, list[tuple[Path, Path]]]:
    if len(pairs) < 2:
        raise ValueError("At least 2 labeled images are required for train/val split")
    shuffled = list(pairs)
    random.Random(seed).shuffle(shuffled)
    val_count = max(1, int(round(len(shuffled) * val_ratio)))
    val_count = min(val_count, len(shuffled) - 1)
    return {"val": shuffled[:val_count], "train": shuffled[val_count:]}


def write_data_yaml(dataset_dir: Path) -> None:
    text = "\n".join(
        [
            "path: data/dataset_yolo/v001_pohon_sono_only_v2",
            "train: images/train",
            "val: images/val",
            "names:",
            "  0: pohon_sono",
            "",
        ]
    )
    (dataset_dir / "data.yaml").write_text(text, encoding="utf-8")


def copy_split(split: dict[str, list[tuple[Path, Path]]], dataset_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for split_name, pairs in split.items():
        image_out = dataset_dir / "images" / split_name
        label_out = dataset_dir / "labels" / split_name
        image_out.mkdir(parents=True, exist_ok=True)
        label_out.mkdir(parents=True, exist_ok=True)
        for image_path, label_path in pairs:
            shutil.copy2(image_path, image_out / image_path.name)
            shutil.copy2(label_path, label_out / label_path.name)
        counts[f"{split_name}_images"] = len(pairs)
        counts[f"{split_name}_labels"] = len(pairs)
    return counts


def write_summary(summary: dict[str, Any], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def build_dataset_v2(
    image_dir: Path,
    label_dir: Path,
    dataset_dir: Path,
    summary_path: Path,
    mode: str = "dry-run",
    seed: int = SAFE_SEED,
) -> dict[str, Any]:
    audit = audit_v001_labels(image_dir, label_dir)
    if audit["status"] == "WAITING_FOR_LABEL_REVIEW":
        summary = {
            "status": "SKIPPED_WAITING_LABELS",
            "audit_status": audit["status"],
            "dataset_dir": str(dataset_dir),
            "mode": mode,
        }
        write_summary(summary, summary_path)
        return summary
    if audit["status"] != "PASS":
        summary = {
            "status": "FAIL_LABEL_AUDIT_NOT_PASS",
            "audit_status": audit["status"],
            "audit_errors": audit.get("errors", []),
            "dataset_dir": str(dataset_dir),
            "mode": mode,
        }
        write_summary(summary, summary_path)
        return summary

    pairs = list_image_label_pairs(image_dir, label_dir)
    split = split_pairs(pairs, seed=seed)
    split_counts = {f"{name}_images": len(items) for name, items in split.items()}
    split_counts.update({f"{name}_labels": len(items) for name, items in split.items()})

    if mode == "dry-run":
        summary = {
            "status": "DATASET_V2_DRY_RUN_READY",
            "mode": mode,
            "seed": seed,
            "dataset_dir": str(dataset_dir),
            "data_yaml": str(dataset_dir / "data.yaml"),
            "total_images": len(pairs),
            "total_boxes": audit["total_boxes"],
            "split_counts": split_counts,
            "class_names": {"0": "pohon_sono"},
            "scope_guard": "V001_ONLY_NO_P001_NO_K001_NO_BOTOL_TEST_DATASET",
        }
        write_summary(summary, summary_path)
        return summary

    if mode != "build":
        raise ValueError("mode must be dry-run or build")

    if dataset_dir.exists() and any(dataset_dir.rglob("*")):
        summary = {
            "status": "DATASET_V2_ALREADY_EXISTS_REFUSE_OVERWRITE",
            "dataset_dir": str(dataset_dir),
            "mode": mode,
        }
        write_summary(summary, summary_path)
        return summary

    dataset_dir.mkdir(parents=True, exist_ok=True)
    copied_counts = copy_split(split, dataset_dir)
    write_data_yaml(dataset_dir)
    summary = {
        "status": "DATASET_V2_BUILD_READY",
        "mode": mode,
        "seed": seed,
        "dataset_dir": str(dataset_dir),
        "data_yaml": str(dataset_dir / "data.yaml"),
        "total_images": len(pairs),
        "total_boxes": audit["total_boxes"],
        "split_counts": copied_counts,
        "class_names": {"0": "pohon_sono"},
        "scope_guard": "V001_ONLY_NO_P001_NO_K001_NO_BOTOL_TEST_DATASET",
    }
    write_summary(summary, summary_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build V001 pohon_sono single-class v2 YOLO dataset.")
    parser.add_argument("--image-dir", default=str(DEFAULT_IMAGE_DIR))
    parser.add_argument("--label-dir", default=str(DEFAULT_LABEL_DIR))
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--mode", choices=["dry-run", "build"], default="dry-run")
    parser.add_argument("--seed", type=int, default=SAFE_SEED)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_dataset_v2(
        image_dir=resolve_project_path(args.image_dir),
        label_dir=resolve_project_path(args.label_dir),
        dataset_dir=resolve_project_path(args.dataset_dir),
        summary_path=resolve_project_path(args.summary),
        mode=args.mode,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(summary["status"])
    return 0 if summary["status"] in {"SKIPPED_WAITING_LABELS", "DATASET_V2_DRY_RUN_READY", "DATASET_V2_BUILD_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
