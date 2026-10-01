from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "data" / "dataset"
DATA_CONFIG = DATASET_ROOT / "data.yaml"
MANIFEST = DATASET_ROOT / "acquisition_manifest.csv"
BASE_MODEL = ROOT / "models" / "yolov8m-seg.pt"
CLASS_NAMES = ("angsana", "konduktor", "struktur_penyangga_sutm")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
LOCAL_DOMAINS = {"Surabaya Utara", "Surabaya Timur", "Surabaya Barat"}
TRAIN_IMAGE_SIZE = 1024
CPU_BATCH_SIZE = 2
MAX_WORKERS = 4


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the canonical vegetation segmentation model.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=TRAIN_IMAGE_SIZE)
    parser.add_argument("--batch", type=int, default=None)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    _validate_dataset()
    if not BASE_MODEL.is_file():
        raise SystemExit(f"Pretrained segmentation model not found: {BASE_MODEL}")

    from ultralytics import YOLO

    device, batch, amp, workers = _training_options(args.device, args.batch)
    model = YOLO(str(BASE_MODEL), task="segment")
    model.train(
        data=str(DATA_CONFIG),
        task="segment",
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=batch,
        device=device,
        amp=amp,
        workers=workers,
        project=str(ROOT / "runs"),
        name="detector",
        exist_ok=True,
        hsv_h=0.01,
        hsv_s=0.3,
        hsv_v=0.2,
        degrees=3.0,
        translate=0.03,
        scale=0.1,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=0.25,
        close_mosaic=10,
        mixup=0.0,
        copy_paste=0.0,
    )
    best = Path(model.trainer.best)
    if not best.is_file():
        raise SystemExit("Training completed without best.pt")

    metrics = YOLO(str(best), task="segment").val(
        data=str(DATA_CONFIG), split="test", imgsz=args.imgsz, device=device, workers=workers, plots=True
    )
    per_class = {}
    for result_index, class_id in enumerate(metrics.ap_class_index):
        values = metrics.class_result(result_index)[-4:]
        per_class[CLASS_NAMES[int(class_id)]] = dict(
            zip(("precision", "recall", "map50", "map50_95"), (round(float(value), 6) for value in values))
        )
    print(
        json.dumps(
            {
                "mask": {
                    "precision": round(float(metrics.seg.mp), 6),
                    "recall": round(float(metrics.seg.mr), 6),
                    "map50": round(float(metrics.seg.map50), 6),
                    "map50_95": round(float(metrics.seg.map), 6),
                    "per_class": per_class,
                },
                "weight": str(best),
                "promoted": False,
            },
            indent=2,
        )
    )


def _validate_dataset() -> None:
    if not DATA_CONFIG.is_file() or not MANIFEST.is_file():
        raise SystemExit("Canonical dataset configuration or acquisition manifest is missing")
    class_map = []
    for line in DATA_CONFIG.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.strip().partition(":")
        if separator and key.isdigit():
            class_map.append(f"{key}: {value.strip()}")
    if class_map != [f"{index}: {name}" for index, name in enumerate(CLASS_NAMES)]:
        raise SystemExit("Dataset class map must be exactly: 0 angsana, 1 konduktor, 2 struktur_penyangga_sutm")

    images: dict[str, tuple[str, Path]] = {}
    for split in ("train", "val", "test"):
        image_dir = DATASET_ROOT / "images" / split
        label_dir = DATASET_ROOT / "labels" / split
        split_images = sorted(path for path in image_dir.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
        if not split_images:
            raise SystemExit(f"Dataset is not ready: add real {split} images and reviewed segmentation labels")
        for image_path in split_images:
            relative = image_path.relative_to(image_dir)
            label_path = (label_dir / relative).with_suffix(".txt")
            if not label_path.is_file():
                raise SystemExit(f"Missing segmentation label for {image_path.relative_to(DATASET_ROOT)}")
            _validate_label(label_path)
            images[image_path.relative_to(DATASET_ROOT).as_posix()] = (split, image_path)
        for label_path in label_dir.rglob("*.txt"):
            relative = label_path.relative_to(label_dir)
            if not any((image_dir / relative).with_suffix(suffix).is_file() for suffix in IMAGE_SUFFIXES):
                raise SystemExit(f"Label has no matching image: {label_path.relative_to(DATASET_ROOT)}")

    rows_by_image: dict[str, dict[str, str]] = {}
    with MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            image_path = row.get("image_path", "").strip().replace("\\", "/")
            if not image_path:
                continue
            if image_path in rows_by_image:
                raise SystemExit(f"Duplicate acquisition manifest row: {image_path}")
            rows_by_image[image_path] = row
    if set(rows_by_image) != set(images):
        raise SystemExit("Every dataset image must have exactly one asset-level acquisition manifest row")

    sessions: dict[str, str] = {}
    scenes: dict[str, str] = {}
    checksums: dict[str, str] = {}
    required = (
        "source_id", "source_type", "provider", "title", "license", "author_or_rights_holder",
        "acquisition_date", "original_class", "mapped_class", "geographic_domain", "viewpoint",
        "capture_session_id", "scene_id", "intended_split", "sha256",
    )
    for image_path, (split, source_path) in images.items():
        row = rows_by_image[image_path]
        if any(not row.get(field, "").strip() for field in required):
            raise SystemExit(f"Incomplete acquisition metadata: {image_path}")
        if not row.get("original_url", "").strip() and not row.get("dataset_identifier", "").strip():
            raise SystemExit(f"Missing source URL or dataset identifier: {image_path}")
        if row["intended_split"].strip() != split:
            raise SystemExit(f"Manifest split does not match image path: {image_path}")
        if row.get("annotation_type") != "yolo_segmentation" or row.get("rights_status") != "approved":
            raise SystemExit(f"Annotation or rights not approved: {image_path}")
        if row.get("download_status") != "downloaded" or row.get("human_review_status") != "approved":
            raise SystemExit(f"Asset is not downloaded and human-reviewed: {image_path}")
        checksum = row["sha256"].strip().lower()
        if checksum != _sha256(source_path):
            raise SystemExit(f"SHA-256 does not match image: {image_path}")
        _claim_checksum(checksums, checksum, image_path)
        mapped_classes = {name.strip() for name in row["mapped_class"].split(";") if name.strip()}
        if not mapped_classes <= set(CLASS_NAMES):
            raise SystemExit(f"Unsupported mapped class: {image_path}")
        if row.get("source_type") == "external" and split != "train":
            raise SystemExit("External images are supplemental train data only")
        if row.get("source_type") == "local" and row.get("geographic_domain") not in LOCAL_DOMAINS:
            raise SystemExit("Local imagery must be from Surabaya Utara, Timur, or Barat")
        if split in {"val", "test"} and (
            row.get("source_type") != "local"
            or row.get("viewpoint") != "ground_level"
            or "Surabaya" not in row.get("geographic_domain", "")
            or "Sidoarjo" in row.get("geographic_domain", "")
        ):
            raise SystemExit("Held-out val/test must be local ground-level Surabaya imagery")
        _claim_split(sessions, row["capture_session_id"].strip(), split, "capture session")
        _claim_split(scenes, row["scene_id"].strip(), split, "scene")


def _validate_label(path: Path) -> None:
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        parts = raw_line.split()
        if len(parts) < 7 or (len(parts) - 1) % 2:
            raise SystemExit(f"Invalid segmentation polygon: {path}:{line_number}")
        try:
            class_id = int(parts[0])
            coordinates = [float(value) for value in parts[1:]]
        except ValueError as exc:
            raise SystemExit(f"Invalid segmentation value: {path}:{line_number}") from exc
        if class_id not in range(len(CLASS_NAMES)) or any(
            not math.isfinite(value) or not 0 <= value <= 1 for value in coordinates
        ):
            raise SystemExit(f"Segmentation class or coordinate out of range: {path}:{line_number}")
        points = list(zip(coordinates[::2], coordinates[1::2]))
        polygon_area = abs(
            sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]))
        ) / 2
        if len(set(points)) < 3 or polygon_area == 0:
            raise SystemExit(f"Degenerate segmentation polygon: {path}:{line_number}")


def _claim_split(seen: dict[str, str], key: str, split: str, label: str) -> None:
    previous = seen.setdefault(key, split)
    if previous != split:
        raise SystemExit(f"The same {label} cannot appear in both {previous} and {split}")


def _training_options(device: str | None, batch: int | None) -> tuple[str | int, int, bool, int]:
    cuda_available = torch.cuda.is_available()
    selected_device: str | int = device or (0 if cuda_available else "cpu")
    if not cuda_available:
        selected_device = "cpu"
    use_cuda = cuda_available and str(selected_device).lower() not in {"cpu", "mps"}
    return selected_device, batch if batch is not None else -1 if use_cuda else CPU_BATCH_SIZE, use_cuda, min(
        MAX_WORKERS, os.cpu_count() or 1
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _claim_checksum(seen: dict[str, str], checksum: str, image_path: str) -> None:
    previous = seen.setdefault(checksum, image_path)
    if previous != image_path:
        raise SystemExit(f"Exact duplicate image: {previous} and {image_path}")


if __name__ == "__main__":
    main()
