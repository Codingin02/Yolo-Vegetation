from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "images_selected"
DEFAULT_LABEL_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "labels_selected"
DEFAULT_SUMMARY_PATH = ROOT / "data" / "metadata" / "progress5_v001_label_audit_summary.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def list_images(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        return []
    return sorted(path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def list_labels(label_dir: Path) -> list[Path]:
    if not label_dir.exists():
        return []
    return sorted(path for path in label_dir.iterdir() if path.is_file() and path.suffix.lower() == ".txt")


def parse_yolo_label_file(path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {"rows": rows, "errors": ["EMPTY_LABEL_FILE"]}

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            errors.append(f"LINE_{line_number}_EMPTY")
            continue
        if "," in stripped:
            errors.append(f"LINE_{line_number}_COMMA_DECIMAL_OR_CSV_NOT_ALLOWED")
            continue
        parts = stripped.split()
        if len(parts) != 5:
            errors.append(f"LINE_{line_number}_EXPECTED_5_COLUMNS")
            continue
        class_token = parts[0]
        if not class_token.isdigit():
            errors.append(f"LINE_{line_number}_CLASS_ID_NOT_INTEGER")
            continue
        class_id = int(class_token)
        if class_id != 0:
            errors.append(f"LINE_{line_number}_NON_POHON_SONO_CLASS_{class_id}")
        try:
            coords = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append(f"LINE_{line_number}_COORDINATE_NOT_FLOAT")
            continue
        if not all(math.isfinite(value) for value in coords):
            errors.append(f"LINE_{line_number}_COORDINATE_NOT_FINITE")
            continue
        x_center, y_center, width, height = coords
        if not all(0.0 <= value <= 1.0 for value in coords):
            errors.append(f"LINE_{line_number}_COORDINATE_OUT_OF_RANGE")
        if width <= 0.0:
            errors.append(f"LINE_{line_number}_WIDTH_NOT_POSITIVE")
        if height <= 0.0:
            errors.append(f"LINE_{line_number}_HEIGHT_NOT_POSITIVE")
        rows.append(
            {
                "line_number": line_number,
                "class_id": class_id,
                "x_center": x_center,
                "y_center": y_center,
                "width": width,
                "height": height,
                "area": width * height,
            }
        )
    return {"rows": rows, "errors": errors}


def write_summary(summary: dict[str, Any], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def audit_v001_labels(image_dir: Path, label_dir: Path, summary_path: Path | None = None) -> dict[str, Any]:
    images = list_images(image_dir)
    labels = list_labels(label_dir)
    image_stems = {path.stem for path in images}
    label_stems = {path.stem for path in labels}

    if not images:
        summary = {
            "status": "NO_SELECTED_IMAGES_FOR_LABEL_AUDIT",
            "image_dir": str(image_dir),
            "label_dir": str(label_dir),
            "image_count": 0,
            "label_count": len(labels),
        }
        if summary_path:
            write_summary(summary, summary_path)
        return summary

    if not labels:
        summary = {
            "status": "WAITING_FOR_LABEL_REVIEW",
            "image_dir": str(image_dir),
            "label_dir": str(label_dir),
            "image_count": len(images),
            "label_count": 0,
            "missing_label_count": len(images),
            "operator_next": "Label images_selected sebagai single-class 0 pohon_sono, lalu simpan ke labels_selected.",
        }
        if summary_path:
            write_summary(summary, summary_path)
        return summary

    missing = sorted(image_stems - label_stems)
    orphan = sorted(label_stems - image_stems)
    bad_files: list[dict[str, Any]] = []
    empty_label_files: list[str] = []
    total_boxes = 0
    total_area = 0.0

    for label_path in labels:
        parsed = parse_yolo_label_file(label_path)
        rows = parsed["rows"]
        errors = parsed["errors"]
        if any(error == "EMPTY_LABEL_FILE" for error in errors):
            empty_label_files.append(label_path.name)
        if errors:
            bad_files.append({"label": str(label_path), "errors": errors})
        total_boxes += len(rows)
        total_area += sum(float(row["area"]) for row in rows)

    errors: list[str] = []
    if missing:
        errors.append("MISSING_LABEL")
    if orphan:
        errors.append("ORPHAN_LABEL")
    if empty_label_files:
        errors.append("EMPTY_LABEL_FILE")
    if bad_files:
        errors.append("BAD_YOLO_ROWS")
    if total_boxes <= 0:
        errors.append("NO_POHON_SONO_BOX")

    status = "PASS" if not errors else "FAIL"
    summary = {
        "status": status,
        "image_dir": str(image_dir),
        "label_dir": str(label_dir),
        "image_count": len(images),
        "label_count": len(labels),
        "missing_label_count": len(missing),
        "orphan_label_count": len(orphan),
        "empty_label_count": len(empty_label_files),
        "bad_file_count": len(bad_files),
        "total_boxes": total_boxes,
        "class_counts": {"0": total_boxes},
        "class_names": {"0": "pohon_sono"},
        "average_box_area": total_area / total_boxes if total_boxes else None,
        "missing_labels": missing,
        "orphan_labels": orphan,
        "empty_label_files": empty_label_files,
        "bad_files": bad_files,
        "errors": errors,
        "single_class_contract": "ONLY_CLASS_0_POHON_SONO_ALLOWED",
    }
    if summary_path:
        write_summary(summary, summary_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit V001 v2 single-class YOLO labels.")
    parser.add_argument("--image-dir", default=str(DEFAULT_IMAGE_DIR))
    parser.add_argument("--label-dir", default=str(DEFAULT_LABEL_DIR))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = audit_v001_labels(resolve_path(args.image_dir), resolve_path(args.label_dir), resolve_path(args.summary))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(summary["status"])
    return 0 if summary["status"] in {"PASS", "WAITING_FOR_LABEL_REVIEW"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
