from __future__ import annotations

import argparse
import sys
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
DEFAULT_DATA = PROJECT_ROOT / "data" / "dataset_yolo" / "field_multiclass_v1" / "data.yaml"
DEFAULT_PROJECT = PROJECT_ROOT / "runs" / "detect"
DEFAULT_NAME = "field_multiclass_v1"


def count_files(folder: Path, extensions: set[str] | None = None) -> int:
    if not folder.exists():
        return 0

    if extensions is None:
        return len([p for p in folder.iterdir() if p.is_file()])

    return len([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in extensions])


def get_stems(folder: Path, extensions: set[str] | None = None) -> set[str]:
    if not folder.exists():
        return set()

    if extensions is None:
        return {p.stem for p in folder.iterdir() if p.is_file()}

    return {p.stem for p in folder.iterdir() if p.is_file() and p.suffix.lower() in extensions}


def dataset_root_from_yaml(data_yaml: Path) -> Path:
    # data.yaml berada di root dataset: field_multiclass_v1/data.yaml
    return data_yaml.parent


def check_dataset(data_yaml: Path) -> tuple[bool, str]:
    if not data_yaml.exists():
        return False, f"DATA_YAML_NOT_FOUND: {data_yaml}"

    dataset_root = dataset_root_from_yaml(data_yaml)

    train_img = dataset_root / "images" / "train"
    val_img = dataset_root / "images" / "val"
    train_lbl = dataset_root / "labels" / "train"
    val_lbl = dataset_root / "labels" / "val"

    required_dirs = [train_img, val_img, train_lbl, val_lbl]
    for folder in required_dirs:
        if not folder.exists():
            return False, f"DATASET_DIR_NOT_FOUND: {folder}"

    train_images = get_stems(train_img, IMAGE_EXTENSIONS)
    val_images = get_stems(val_img, IMAGE_EXTENSIONS)
    train_labels = get_stems(train_lbl, {".txt"})
    val_labels = get_stems(val_lbl, {".txt"})

    if not train_images:
        return False, "NO_TRAIN_IMAGES"

    if not val_images:
        return False, "NO_VAL_IMAGES"

    if train_images != train_labels:
        missing = sorted(train_images - train_labels)
        orphan = sorted(train_labels - train_images)
        return False, f"TRAIN_IMAGE_LABEL_MISMATCH missing={len(missing)} orphan={len(orphan)}"

    if val_images != val_labels:
        missing = sorted(val_images - val_labels)
        orphan = sorted(val_labels - val_images)
        return False, f"VAL_IMAGE_LABEL_MISMATCH missing={len(missing)} orphan={len(orphan)}"

    return True, "dataset has matching train/val image-label counts"


def parse_batch(value: str):
    if value.lower() == "auto":
        return "auto"

    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--batch harus integer atau auto") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safe YOLOv8 launcher using Ultralytics Python API. Default is dry-run."
    )
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", default="auto")
    parser.add_argument("--device", default="0")
    parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Explicitly run training after readiness checks.",
    )

    args = parser.parse_args()

    data_yaml = Path(args.data).resolve()
    project_dir = Path(args.project).resolve()

    dataset_ok, reason = check_dataset(data_yaml)

    print(f"dataset_status: {'READY' if dataset_ok else 'DATASET_NOT_READY'}")
    print(f"reason: {reason}")

    command_preview = (
        f"YOLO('{args.model}').train("
        f"data=r'{data_yaml}', "
        f"epochs={args.epochs}, "
        f"imgsz={args.imgsz}, "
        f"batch={args.batch}, "
        f"device='{args.device}', "
        f"project=r'{project_dir}', "
        f"name='{args.name}'"
        f")"
    )

    print("command_preview:")
    print(command_preview)

    if not dataset_ok:
        print("result: DATASET_NOT_READY")
        return 1

    if args.dry_run or not args.run:
        print("result: DRY_RUN_READY")
        print("note: tambahkan --run untuk menjalankan training aktual.")
        return 0

    try:
        from ultralytics import YOLO
    except Exception as exc:
        print("result: ULTRALYTICS_IMPORT_FAILED")
        print(f"error: {exc}")
        print("fix: pastikan ultralytics terinstall di venv project.")
        return 1

    batch = parse_batch(str(args.batch))

    print("result: TRAINING_STARTED")
    print("warning: ini smoke training, bukan model final dan tidak boleh diklaim sebagai akurasi final.")

    model = YOLO(args.model)
    results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=batch,
        device=args.device,
        project=str(project_dir),
        name=args.name,
        exist_ok=False,
    )

    print("result: TRAINING_FINISHED")
    print(f"output_project: {project_dir}")
    print(f"run_name: {args.name}")
    print("note: cek folder runs/detect untuk best.pt dan hasil training.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
