"""Dataset split builder for field_multiclass_v1, dry-run first."""

from __future__ import annotations

import argparse
import csv
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

from .classes import CLASS_ORDER
from .metadata import list_images
from .paths import DEFAULT_POINT, FIELD_DATASET_DIR, METADATA_DIR, image_dir_for_point, label_dir_for_point
from .yolo_validate import validate_dataset


@dataclass(frozen=True)
class DatasetPair:
    image: Path
    label: Path


@dataclass
class BuildSummary:
    status: str
    total_pairs: int
    train_count: int
    val_count: int
    target_dir: Path


def collect_pairs(point: str = DEFAULT_POINT) -> list[DatasetPair]:
    image_dir = image_dir_for_point(point)
    label_dir = label_dir_for_point(point)
    images = list_images(image_dir)
    pairs: list[DatasetPair] = []
    for image in images:
        label = label_dir / f"{image.stem}.txt"
        if label.exists():
            pairs.append(DatasetPair(image=image, label=label))
    return pairs


def split_pairs(pairs: list[DatasetPair], val_ratio: float, seed: int) -> tuple[list[DatasetPair], list[DatasetPair]]:
    if not 0.0 < val_ratio < 1.0:
        raise ValueError("val_ratio must be between 0 and 1")
    shuffled = list(pairs)
    random.Random(seed).shuffle(shuffled)
    val_count = max(1, int(round(len(shuffled) * val_ratio))) if len(shuffled) > 1 else 0
    val_pairs = shuffled[:val_count]
    train_pairs = shuffled[val_count:]
    return train_pairs, val_pairs


def write_data_yaml(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    output = target_dir / "data.yaml"
    lines = [
        f"path: {target_dir.resolve().as_posix()}",
        "train: images/train",
        "val: images/val",
        "names:",
    ]
    for class_id, name in CLASS_ORDER.items():
        lines.append(f"  {class_id}: {name}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _copy_pair(pair: DatasetPair, target_dir: Path, split_name: str, overwrite: bool) -> None:
    image_target = target_dir / "images" / split_name / pair.image.name
    label_target = target_dir / "labels" / split_name / pair.label.name
    image_target.parent.mkdir(parents=True, exist_ok=True)
    label_target.parent.mkdir(parents=True, exist_ok=True)
    for source, target in ((pair.image, image_target), (pair.label, label_target)):
        if target.exists() and not overwrite:
            continue
        shutil.copy2(source, target)


def write_build_manifest(train_pairs: list[DatasetPair], val_pairs: list[DatasetPair], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["split", "image", "label"])
        for split_name, pairs in (("train", train_pairs), ("val", val_pairs)):
            for pair in pairs:
                writer.writerow([split_name, pair.image.name, pair.label.name])


def build_dataset(
    point: str,
    target_dir: Path,
    val_ratio: float,
    seed: int,
    mode: str = "dry-run",
    force: bool = False,
    overwrite: bool = False,
) -> BuildSummary:
    if mode not in {"dry-run", "build"}:
        raise ValueError("mode must be dry-run or build")
    validation = validate_dataset(image_dir_for_point(point), label_dir_for_point(point))
    if not validation.valid and not force:
        return BuildSummary("LABELS_NOT_READY", 0, 0, 0, target_dir)
    pairs = collect_pairs(point)
    if not pairs:
        return BuildSummary("LABELS_NOT_READY", 0, 0, 0, target_dir)
    train_pairs, val_pairs = split_pairs(pairs, val_ratio=val_ratio, seed=seed)
    if mode == "build":
        for pair in train_pairs:
            _copy_pair(pair, target_dir, "train", overwrite=overwrite)
        for pair in val_pairs:
            _copy_pair(pair, target_dir, "val", overwrite=overwrite)
        write_data_yaml(target_dir)
        write_build_manifest(train_pairs, val_pairs, METADATA_DIR / "field_multiclass_v1_split_manifest.csv")
    return BuildSummary(
        status="DRY_RUN_READY" if mode == "dry-run" else "BUILT",
        total_pairs=len(pairs),
        train_count=len(train_pairs),
        val_count=len(val_pairs),
        target_dir=target_dir,
    )


def format_summary(summary: BuildSummary) -> str:
    return "\n".join(
        [
            f"status: {summary.status}",
            f"total_pairs: {summary.total_pairs}",
            f"train_count: {summary.train_count}",
            f"val_count: {summary.val_count}",
            f"target_dir: {summary.target_dir}",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build field_multiclass_v1 dataset after labels pass validation.")
    parser.add_argument("--point", default=DEFAULT_POINT)
    parser.add_argument("--target-dir", type=Path, default=FIELD_DATASET_DIR)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=23050874166)
    parser.add_argument("--mode", choices=["dry-run", "build"], default="dry-run")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = build_dataset(
        point=args.point,
        target_dir=args.target_dir,
        val_ratio=args.val_ratio,
        seed=args.seed,
        mode=args.mode,
        force=args.force,
        overwrite=args.overwrite,
    )
    print(format_summary(summary))
    return 0 if summary.status in {"DRY_RUN_READY", "BUILT"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
