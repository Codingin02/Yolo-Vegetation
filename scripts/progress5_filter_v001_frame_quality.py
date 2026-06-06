from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "images_all"
DEFAULT_SELECTED_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "images_selected"
DEFAULT_REJECTED_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "images_rejected"
DEFAULT_SUMMARY_PATH = ROOT / "data" / "metadata" / "progress5_v001_quality_filter_summary.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def list_images(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        return []
    return sorted(path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def hamming_distance(left: int, right: int) -> int:
    return int((left ^ right).bit_count())


def average_hash(gray_image: Any, cv2_module: Any) -> int:
    resized = cv2_module.resize(gray_image, (8, 8), interpolation=cv2_module.INTER_AREA)
    mean_value = float(resized.mean())
    bits = resized > mean_value
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bool(bit))
    return value


def write_summary(summary: dict[str, Any], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def copy_without_overwrite(source: Path, destination_dir: Path) -> bool:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    if destination.exists():
        return False
    shutil.copy2(source, destination)
    return True


def filter_frames(
    input_dir: Path,
    selected_dir: Path,
    rejected_dir: Path,
    summary_path: Path,
    blur_min: float = 80.0,
    brightness_min: float = 35.0,
    brightness_max: float = 235.0,
    duplicate_hamming_max: int = 4,
) -> dict[str, Any]:
    try:
        import cv2  # type: ignore
    except Exception as exc:  # pragma: no cover - environment guard
        summary = {
            "status": "QUALITY_FILTER_FAILED_OPENCV_NOT_AVAILABLE",
            "error": str(exc),
            "input_dir": str(input_dir),
        }
        write_summary(summary, summary_path)
        return summary

    images = list_images(input_dir)
    selected_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir.mkdir(parents=True, exist_ok=True)

    if not images:
        summary = {
            "status": "NO_FRAMES_FOR_QUALITY_FILTER",
            "input_dir": str(input_dir),
            "selected_dir": str(selected_dir),
            "rejected_dir": str(rejected_dir),
            "selected_count": 0,
            "rejected_count": 0,
        }
        write_summary(summary, summary_path)
        return summary

    selected_hashes: list[tuple[str, int]] = []
    records: list[dict[str, Any]] = []
    selected_count = 0
    rejected_count = 0
    selected_existing = 0
    rejected_existing = 0

    for image_path in images:
        image = cv2.imread(str(image_path))
        reasons: list[str] = []
        blur_score: float | None = None
        brightness_mean: float | None = None
        duplicate_of: str | None = None
        duplicate_distance: int | None = None

        if image is None:
            reasons.append("CORRUPT_OR_UNREADABLE_IMAGE")
            image_hash: int | None = None
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            brightness_mean = float(gray.mean())
            image_hash = average_hash(gray, cv2)
            if blur_score < blur_min:
                reasons.append("BLUR_LOW")
            if brightness_mean < brightness_min:
                reasons.append("TOO_DARK")
            if brightness_mean > brightness_max:
                reasons.append("TOO_BRIGHT")
            for selected_name, selected_hash in selected_hashes:
                distance = hamming_distance(image_hash, selected_hash)
                if duplicate_distance is None or distance < duplicate_distance:
                    duplicate_distance = distance
                    duplicate_of = selected_name
                if distance <= duplicate_hamming_max:
                    reasons.append("DUPLICATE_SIMILAR")
                    break

        accepted = not reasons and image_hash is not None
        if accepted:
            copied = copy_without_overwrite(image_path, selected_dir)
            selected_count += 1
            selected_existing += 0 if copied else 1
            selected_hashes.append((image_path.name, image_hash))
            destination = str(selected_dir / image_path.name)
        else:
            copied = copy_without_overwrite(image_path, rejected_dir)
            rejected_count += 1
            rejected_existing += 0 if copied else 1
            destination = str(rejected_dir / image_path.name)

        records.append(
            {
                "image": str(image_path),
                "decision": "SELECTED_FOR_MANUAL_LABEL_REVIEW" if accepted else "REJECTED_QUALITY_FILTER",
                "destination": destination,
                "copied": copied,
                "blur_score_laplacian": blur_score,
                "brightness_mean": brightness_mean,
                "duplicate_of": duplicate_of if "DUPLICATE_SIMILAR" in reasons else None,
                "duplicate_distance": duplicate_distance,
                "reasons": reasons,
            }
        )

    summary = {
        "status": "QUALITY_FILTER_COMPLETE",
        "input_dir": str(input_dir),
        "selected_dir": str(selected_dir),
        "rejected_dir": str(rejected_dir),
        "summary_path": str(summary_path),
        "blur_min": blur_min,
        "brightness_min": brightness_min,
        "brightness_max": brightness_max,
        "duplicate_hamming_max": duplicate_hamming_max,
        "images_seen": len(images),
        "selected_count": selected_count,
        "rejected_count": rejected_count,
        "selected_existing": selected_existing,
        "rejected_existing": rejected_existing,
        "manual_review_required": "TREE_PRESENCE_AND_CANOPY_TIGHTNESS_REVIEW_REQUIRED",
        "source_policy": "COPY_ONLY_NO_SOURCE_DELETE_OR_MOVE",
        "records": records,
    }
    write_summary(summary, summary_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Filter V001 v2 frames for blur, brightness, and duplicate risk.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--selected-dir", default=str(DEFAULT_SELECTED_DIR))
    parser.add_argument("--rejected-dir", default=str(DEFAULT_REJECTED_DIR))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--blur-min", type=float, default=80.0)
    parser.add_argument("--brightness-min", type=float, default=35.0)
    parser.add_argument("--brightness-max", type=float, default=235.0)
    parser.add_argument("--duplicate-hamming-max", type=int, default=4)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = filter_frames(
        input_dir=resolve_path(args.input_dir),
        selected_dir=resolve_path(args.selected_dir),
        rejected_dir=resolve_path(args.rejected_dir),
        summary_path=resolve_path(args.summary),
        blur_min=args.blur_min,
        brightness_min=args.brightness_min,
        brightness_max=args.brightness_max,
        duplicate_hamming_max=args.duplicate_hamming_max,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(summary["status"])
    return 0 if summary["status"] == "QUALITY_FILTER_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
