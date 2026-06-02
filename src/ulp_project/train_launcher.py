"""YOLOv8 training launcher that is dry-run by default."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .paths import FIELD_DATA_YAML, PROJECT_ROOT


@dataclass
class TrainingReadiness:
    status: str
    reason: str
    train_images: int = 0
    train_labels: int = 0
    val_images: int = 0
    val_labels: int = 0


def check_dataset_ready(data_yaml: Path) -> TrainingReadiness:
    if not data_yaml.exists():
        return TrainingReadiness("DATASET_NOT_READY", f"missing data.yaml: {data_yaml}")
    root = data_yaml.parent
    train_images = list((root / "images" / "train").glob("*")) if (root / "images" / "train").exists() else []
    val_images = list((root / "images" / "val").glob("*")) if (root / "images" / "val").exists() else []
    train_labels = list((root / "labels" / "train").glob("*.txt")) if (root / "labels" / "train").exists() else []
    val_labels = list((root / "labels" / "val").glob("*.txt")) if (root / "labels" / "val").exists() else []
    if not train_images or not val_images:
        return TrainingReadiness("DATASET_NOT_READY", "train/val images are not ready")
    if len(train_images) != len(train_labels) or len(val_images) != len(val_labels):
        return TrainingReadiness(
            "DATASET_NOT_READY",
            "image/label counts do not match",
            len(train_images),
            len(train_labels),
            len(val_images),
            len(val_labels),
        )
    return TrainingReadiness(
        "READY",
        "dataset has matching train/val image-label counts",
        len(train_images),
        len(train_labels),
        len(val_images),
        len(val_labels),
    )


def build_train_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        "-m",
        "ultralytics",
        "train",
        f"model={args.model}",
        f"data={args.data}",
        f"epochs={args.epochs}",
        f"imgsz={args.imgsz}",
        f"batch={args.batch}",
        f"device={args.device}",
        f"project={PROJECT_ROOT / 'runs' / 'detect'}",
        "name=field_multiclass_v1",
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe YOLOv8 launcher. Default is dry-run.")
    parser.add_argument("--data", type=Path, default=FIELD_DATA_YAML)
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", default="auto")
    parser.add_argument("--device", default="0")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--run", action="store_true", help="Explicitly run training after readiness checks.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    readiness = check_dataset_ready(args.data)
    print(f"dataset_status: {readiness.status}")
    print(f"reason: {readiness.reason}")
    if readiness.status != "READY":
        print("result: DATASET_NOT_READY")
        return 1 if args.run else 0
    command = build_train_command(args)
    print("command:")
    print(" ".join(str(part) for part in command))
    if not args.run:
        print("result: DRY_RUN_READY")
        return 0
    try:
        import ultralytics  # noqa: F401
    except ImportError:
        print("dependency_missing: ultralytics")
        print("install_hint: python -m pip install ultralytics")
        return 1
    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
