"""Reusable YOLO label audit helpers for V001 recovery work."""

from __future__ import annotations

import math
import statistics
from pathlib import Path
from typing import Any

from .classes import CLASS_ORDER

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
HUGE_BOX_AREA_THRESHOLD = 0.85
TINY_BOX_AREA_THRESHOLD = 0.0004
EDGE_MARGIN_THRESHOLD = 0.01


def read_yolo_label_file(path: Path | str) -> dict[str, Any]:
    label_path = Path(path)
    result: dict[str, Any] = {
        "path": str(label_path),
        "status": "VALID",
        "box_count": 0,
        "class_counts": {},
        "boxes": [],
        "warnings": [],
        "errors": [],
    }
    if not label_path.exists():
        result["status"] = "INVALID"
        result["errors"].append({"code": "LABEL_FILE_NOT_FOUND", "line": 0, "detail": str(label_path)})
        return result

    lines = label_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    non_empty_seen = False
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        non_empty_seen = True
        parts = stripped.split()
        if len(parts) != 5:
            result["errors"].append(
                {
                    "code": "BAD_COLUMN_COUNT",
                    "line": line_number,
                    "detail": f"expected 5 got {len(parts)}",
                }
            )
            continue
        try:
            class_id = int(parts[0])
        except ValueError:
            result["errors"].append({"code": "BAD_CLASS_ID", "line": line_number, "detail": parts[0]})
            continue
        try:
            x_center, y_center, width, height = [float(value) for value in parts[1:]]
        except ValueError:
            result["errors"].append({"code": "BAD_FLOAT", "line": line_number, "detail": " ".join(parts[1:])})
            continue
        values = [x_center, y_center, width, height]
        if not all(math.isfinite(value) for value in values):
            result["errors"].append({"code": "NON_FINITE_COORDINATE", "line": line_number, "detail": " ".join(parts[1:])})
            continue
        if not all(0.0 <= value <= 1.0 for value in values):
            result["errors"].append({"code": "COORDINATE_OUT_OF_RANGE", "line": line_number, "detail": " ".join(parts[1:])})
            continue
        if width <= 0.0 or height <= 0.0:
            result["errors"].append({"code": "NON_POSITIVE_SIZE", "line": line_number, "detail": f"{width} {height}"})
            continue

        left = x_center - width / 2.0
        right = x_center + width / 2.0
        top = y_center - height / 2.0
        bottom = y_center + height / 2.0
        if left < 0.0 or right > 1.0 or top < 0.0 or bottom > 1.0:
            result["errors"].append(
                {
                    "code": "BBOX_EXTENDS_OUTSIDE_IMAGE",
                    "line": line_number,
                    "detail": f"left={left:.6f} top={top:.6f} right={right:.6f} bottom={bottom:.6f}",
                }
            )
            continue

        area = width * height
        box = {
            "line": line_number,
            "class_id": class_id,
            "x_center": x_center,
            "y_center": y_center,
            "width": width,
            "height": height,
            "area": area,
        }
        result["boxes"].append(box)
        result["box_count"] += 1
        result["class_counts"][class_id] = result["class_counts"].get(class_id, 0) + 1

        margin = min(left, top, 1.0 - right, 1.0 - bottom)
        if area < TINY_BOX_AREA_THRESHOLD:
            result["warnings"].append({"code": "BBOX_TOO_SMALL_REVIEW", "line": line_number, "area": area})
        if area > HUGE_BOX_AREA_THRESHOLD:
            result["warnings"].append({"code": "HUGE_BOX_DOMINANCE", "line": line_number, "area": area})
        if margin <= EDGE_MARGIN_THRESHOLD:
            result["warnings"].append({"code": "BBOX_TOUCHES_IMAGE_EDGE_REVIEW", "line": line_number, "margin": margin})

    if not non_empty_seen:
        result["status"] = "EMPTY_LABEL"
        result["warnings"].append({"code": "EMPTY_LABEL_FILE", "line": 0})
    elif result["errors"]:
        result["status"] = "INVALID"
    return result


def audit_yolo_folder(image_dir: Path | str, label_dir: Path | str, class_names: dict[int, str] | list[str]) -> dict[str, Any]:
    image_root = Path(image_dir)
    label_root = Path(label_dir)
    classes = _normalize_class_names(class_names)
    images = sorted(path for path in image_root.glob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS) if image_root.exists() else []
    labels = sorted(path for path in label_root.glob("*.txt") if path.is_file()) if label_root.exists() else []
    image_stems = {path.stem for path in images}
    label_stems = {path.stem for path in labels}
    missing = sorted(image_stems - label_stems)
    orphan = sorted(label_stems - image_stems)

    class_counts = {class_id: 0 for class_id in classes}
    label_results = []
    errors = []
    warnings = []
    empty_labels = []
    box_areas = []
    for label in labels:
        parsed = read_yolo_label_file(label)
        label_results.append(parsed)
        if parsed["status"] == "EMPTY_LABEL":
            empty_labels.append(label.name)
        for class_id, count in parsed["class_counts"].items():
            class_counts[class_id] = class_counts.get(class_id, 0) + count
        for box in parsed["boxes"]:
            box_areas.append(float(box["area"]))
            if int(box["class_id"]) not in classes:
                errors.append({"code": "CLASS_ID_OUT_OF_RANGE", "file": str(label), "line": box["line"], "class_id": box["class_id"]})
        for item in parsed["errors"]:
            errors.append({"file": str(label), **item})
        for item in parsed["warnings"]:
            warnings.append({"file": str(label), **item})

    for stem in missing:
        errors.append({"code": "MISSING_LABEL", "stem": stem})
    for stem in orphan:
        errors.append({"code": "ORPHAN_LABEL", "stem": stem})

    risk_warnings = _class_risk_warnings(class_counts, classes)
    warnings.extend(risk_warnings)
    area_stats = _area_stats_from_values(box_areas)
    if area_stats["huge_box_count"] > 0:
        warnings.append(
            {
                "code": "HUGE_BOX_DOMINANCE",
                "huge_box_count": area_stats["huge_box_count"],
                "max_area": area_stats["max_area"],
            }
        )

    status = "VALID"
    if errors:
        status = "INVALID"
    elif warnings:
        status = "VALID_WITH_WARNINGS"
    return {
        "status": status,
        "image_dir": str(image_root),
        "label_dir": str(label_root),
        "image_count": len(images),
        "label_count": len(labels),
        "missing_labels": missing,
        "orphan_labels": orphan,
        "empty_labels": empty_labels,
        "bad_row_count": sum(1 for error in errors if error.get("code") not in {"MISSING_LABEL", "ORPHAN_LABEL"}),
        "class_counts": class_counts,
        "box_area_stats": area_stats,
        "warnings": warnings,
        "errors": errors,
        "label_results": label_results,
    }


def compute_class_distribution(label_dir: Path | str) -> dict[str, Any]:
    label_root = Path(label_dir)
    counts: dict[int, int] = {}
    bad_rows = 0
    label_files = sorted(label_root.glob("*.txt")) if label_root.exists() else []
    for label in label_files:
        parsed = read_yolo_label_file(label)
        for class_id, count in parsed["class_counts"].items():
            counts[class_id] = counts.get(class_id, 0) + count
        bad_rows += len(parsed["errors"])
    return {
        "status": "VALID" if bad_rows == 0 else "INVALID",
        "label_dir": str(label_root),
        "label_file_count": len(label_files),
        "total_boxes": sum(counts.values()),
        "class_counts": dict(sorted(counts.items())),
        "bad_row_count": bad_rows,
    }


def compute_box_area_stats(label_dir: Path | str) -> dict[str, Any]:
    areas = []
    for label in sorted(Path(label_dir).glob("*.txt")) if Path(label_dir).exists() else []:
        parsed = read_yolo_label_file(label)
        areas.extend(float(box["area"]) for box in parsed["boxes"])
    stats = _area_stats_from_values(areas)
    warnings = []
    if stats["huge_box_count"] > 0:
        warnings.append({"code": "HUGE_BOX_DOMINANCE", "max_area": stats["max_area"], "huge_box_count": stats["huge_box_count"]})
    stats["warnings"] = warnings
    stats["status"] = "VALID_WITH_WARNINGS" if warnings else "VALID"
    return stats


def detect_class_coverage_risk(
    train_label_dir: Path | str,
    val_label_dir: Path | str,
    min_instances_per_class: int = 10,
) -> dict[str, Any]:
    train = compute_class_distribution(train_label_dir)
    val = compute_class_distribution(val_label_dir)
    class_ids = sorted(set(train["class_counts"]) | set(val["class_counts"]))
    per_class = {}
    warnings = []
    total_counts = []
    for class_id in class_ids:
        train_count = int(train["class_counts"].get(class_id, 0))
        val_count = int(val["class_counts"].get(class_id, 0))
        total = train_count + val_count
        total_counts.append(total)
        per_class[class_id] = {"train": train_count, "val": val_count, "total": total}
        if total < min_instances_per_class:
            warnings.append({"code": "CLASS_UNDERREPRESENTED", "class_id": class_id, "total": total, "minimum": min_instances_per_class})
        if val_count == 0:
            warnings.append({"code": "CLASS_MISSING_IN_VALIDATION", "class_id": class_id, "val": val_count})

    positive = [count for count in total_counts if count > 0]
    if positive and max(positive) > min(positive) * 3:
        warnings.append({"code": "EXTREME_CLASS_IMBALANCE", "min_count": min(positive), "max_count": max(positive)})
    if warnings and len(class_ids) > 1:
        warnings.append({"code": "MULTICLASS_NOT_READY", "reason": "class coverage and validation distribution are not reliable"})
    return {
        "status": "MULTICLASS_NOT_READY" if any(item["code"] == "MULTICLASS_NOT_READY" for item in warnings) else "CLASS_COVERAGE_OK",
        "train_label_dir": str(train_label_dir),
        "val_label_dir": str(val_label_dir),
        "min_instances_per_class": min_instances_per_class,
        "per_class": per_class,
        "warnings": warnings,
        "errors": [],
    }


def _normalize_class_names(class_names: dict[int, str] | list[str]) -> dict[int, str]:
    if isinstance(class_names, dict):
        return {int(key): value for key, value in class_names.items()}
    return {index: name for index, name in enumerate(class_names)}


def _class_risk_warnings(class_counts: dict[int, int], class_names: dict[int, str], min_instances: int = 10) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    counts = []
    for class_id, class_name in class_names.items():
        count = int(class_counts.get(class_id, 0))
        counts.append(count)
        if count < min_instances:
            warnings.append(
                {
                    "code": "CLASS_UNDERREPRESENTED",
                    "class_id": class_id,
                    "class_name": class_name,
                    "count": count,
                    "minimum": min_instances,
                }
            )
    positive = [count for count in counts if count > 0]
    if len(positive) > 1 and max(positive) > min(positive) * 3:
        warnings.append({"code": "EXTREME_CLASS_IMBALANCE", "min_count": min(positive), "max_count": max(positive)})
    if len(class_names) > 1 and any(item["code"] in {"CLASS_UNDERREPRESENTED", "EXTREME_CLASS_IMBALANCE"} for item in warnings):
        warnings.append({"code": "MULTICLASS_NOT_READY", "reason": "dataset is technically valid but not reliable for multiclass runtime"})
    return warnings


def _area_stats_from_values(areas: list[float]) -> dict[str, Any]:
    if not areas:
        return {
            "box_count": 0,
            "min_area": None,
            "median_area": None,
            "mean_area": None,
            "max_area": None,
            "huge_box_count": 0,
            "huge_box_share": 0.0,
        }
    sorted_areas = sorted(areas)
    huge_count = sum(1 for area in sorted_areas if area > HUGE_BOX_AREA_THRESHOLD)
    return {
        "box_count": len(sorted_areas),
        "min_area": min(sorted_areas),
        "median_area": statistics.median(sorted_areas),
        "mean_area": statistics.fmean(sorted_areas),
        "max_area": max(sorted_areas),
        "huge_box_count": huge_count,
        "huge_box_share": huge_count / len(sorted_areas),
    }


DEFAULT_CLASS_NAMES = dict(CLASS_ORDER)
