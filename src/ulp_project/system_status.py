"""Read-only project status orchestration for Phase 4."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .classes import CLASS_ORDER
from .metadata import IMAGE_EXTENSIONS
from .paths import PROJECT_ROOT


def _read_class_order(config_path: Path) -> dict[int, str]:
    if not config_path.exists():
        return {}
    parsed: dict[int, str] = {}
    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key.isdigit() and value:
            parsed[int(key)] = value
    return parsed


def _count_images(path: Path) -> tuple[int, list[str]]:
    if not path.exists():
        return 0, []
    images = sorted(
        item.name
        for item in path.iterdir()
        if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
    )
    return len(images), images


def _count_labels(path: Path) -> tuple[int, list[str]]:
    if not path.exists():
        return 0, []
    labels = sorted(
        item.name
        for item in path.iterdir()
        if item.is_file() and item.suffix.lower() == ".txt" and item.name.lower() != "classes.txt"
    )
    return len(labels), labels


def _dataset_split_counts(dataset_dir: Path) -> dict[str, int | bool]:
    train_images = dataset_dir / "images" / "train"
    val_images = dataset_dir / "images" / "val"
    train_labels = dataset_dir / "labels" / "train"
    val_labels = dataset_dir / "labels" / "val"

    def count_files(path: Path, suffixes: set[str] | None = None) -> int:
        if not path.exists():
            return 0
        return sum(
            1
            for item in path.iterdir()
            if item.is_file() and (suffixes is None or item.suffix.lower() in suffixes)
        )

    return {
        "dataset_dir_exists": dataset_dir.exists(),
        "train_image_count": count_files(train_images, IMAGE_EXTENSIONS),
        "val_image_count": count_files(val_images, IMAGE_EXTENSIONS),
        "train_label_count": count_files(train_labels, {".txt"}),
        "val_label_count": count_files(val_labels, {".txt"}),
    }


def collect_project_status(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    project_root = Path(project_root)
    data_dir = project_root / "data"
    image_dir = data_dir / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "images_selected"
    label_dir = data_dir / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "labels_selected"
    export_dir = data_dir / "exports" / "make_sense" / "V001_pohon_sono"
    dataset_dir = data_dir / "dataset_yolo" / "field_multiclass_v1"
    data_yaml = dataset_dir / "data.yaml"
    config_class_order = _read_class_order(project_root / "configs" / "classes.yaml")

    image_count, images = _count_images(image_dir)
    label_count, labels = _count_labels(label_dir)
    export_label_count, export_labels = _count_labels(export_dir)

    image_stems = {Path(name).stem for name in images}
    label_stems = {Path(name).stem for name in labels}
    missing_labels = sorted(image_stems - label_stems)
    orphan_labels = sorted(label_stems - image_stems)
    labels_ready = image_count > 0 and not missing_labels and not orphan_labels

    dataset_counts = _dataset_split_counts(dataset_dir)
    data_yaml_exists = data_yaml.exists()

    if labels_ready:
        label_status = "LABELS_READY"
    elif export_label_count > 0:
        label_status = "READY_FOR_LABEL_IMPORT"
    else:
        label_status = "WAITING_FOR_LABELS"

    dataset_ready = bool(
        data_yaml_exists
        and dataset_counts["train_image_count"]
        and dataset_counts["val_image_count"]
        and dataset_counts["train_image_count"] == dataset_counts["train_label_count"]
        and dataset_counts["val_image_count"] == dataset_counts["val_label_count"]
    )

    return {
        "project_root": str(project_root),
        "class_order": config_class_order,
        "class_order_ok": config_class_order == CLASS_ORDER,
        "review_point": "V001_pohon_sono",
        "images_selected": {
            "path": str(image_dir),
            "exists": image_dir.exists(),
            "image_count": image_count,
        },
        "labels_selected": {
            "path": str(label_dir),
            "exists": label_dir.exists(),
            "label_count": label_count,
            "missing_label_count": len(missing_labels),
            "orphan_label_count": len(orphan_labels),
            "status": label_status,
        },
        "makesense_export": {
            "path": str(export_dir),
            "exists": export_dir.exists(),
            "label_count": export_label_count,
            "status": "EXPORT_READY_FOR_DRY_RUN" if export_label_count else "BLOCKED_WAITING_FOR_MAKESENSE_EXPORT",
        },
        "field_dataset": {
            "path": str(dataset_dir),
            "data_yaml_exists": data_yaml_exists,
            "dataset_ready": dataset_ready,
            **dataset_counts,
            "status": "READY_FOR_TRAIN_DRY_RUN" if dataset_ready else "DATASET_NOT_READY",
        },
        "components": {
            "flask_scaffold": (project_root / "src" / "ulp_project" / "flask_app.py").exists(),
            "map_builder": (project_root / "src" / "ulp_project" / "map_builder.py").exists(),
            "spreadsheet_exporter": (project_root / "src" / "ulp_project" / "spreadsheet_export.py").exists(),
            "environmental_risk_schema": (project_root / "configs" / "environmental_risk_schema.yaml").exists(),
        },
        "overall_status": "READY_FOR_DATASET_BUILD" if labels_ready else "WAITING_FOR_LABELS",
        "blocked_items": [
            item
            for item, blocked in {
                "makesense_export": export_label_count == 0,
                "label_validation": not labels_ready,
                "dataset_build": not labels_ready,
                "training": not dataset_ready,
            }.items()
            if blocked
        ],
    }


def render_status_text(status: dict[str, Any]) -> str:
    labels = status["labels_selected"]
    export = status["makesense_export"]
    dataset = status["field_dataset"]
    lines = [
        "ULP Project System Status",
        f"overall_status: {status['overall_status']}",
        f"class_order_ok: {status['class_order_ok']}",
        f"images_selected_count: {status['images_selected']['image_count']}",
        f"labels_selected_count: {labels['label_count']}",
        f"missing_label_count: {labels['missing_label_count']}",
        f"makesense_export_label_count: {export['label_count']}",
        f"data_yaml_exists: {dataset['data_yaml_exists']}",
        f"dataset_status: {dataset['status']}",
        "blocked_items: " + ", ".join(status["blocked_items"]),
    ]
    return "\n".join(lines)


def render_status_markdown(status: dict[str, Any]) -> str:
    text = render_status_text(status)
    return "# Phase 4 Current System Status\n\n```text\n" + text + "\n```\n"
