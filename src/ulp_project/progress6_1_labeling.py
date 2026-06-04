"""Progress 6.1 labeling handoff and YOLO dataset validation helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .classes import CLASS_ORDER, CLASS_NAMES
from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT

SEED = 23050874166
DATASET_ROOT = PROJECT_ROOT / "data" / "dataset_yolo"
REVIEW_POINT = "V001_pohon_sono"
REVIEW_POINT_DIR = DATASET_ROOT / "00_review_candidates" / REVIEW_POINT
MAKESENSE_EXPORT_DIR = DATASET_ROOT / "01_makesense_export"
LEGACY_MAKESENSE_EXPORT_DIR = PROJECT_ROOT / "data" / "exports" / "make_sense"
LABEL_AUDIT_DIR = DATASET_ROOT / "02_label_audit"
DATASET_BUILD_DIR = DATASET_ROOT / "03_dataset_build"
FIELD_DATASET_DIR = DATASET_ROOT / "field_multiclass_v1"
CLASS_ORDER_CONFIG = PROJECT_ROOT / "configs" / "yolo_class_order.yaml"
YOLO_CLASSES_TEMPLATE = PROJECT_ROOT / "data" / "templates" / "yolo_classes.txt"
LOCAL_MODEL_RUNTIME_EXAMPLE = PROJECT_ROOT / "configs" / "local_model_runtime_paths.example.yaml"
MODEL_RUNTIME_CONFIG = PROJECT_ROOT / "configs" / "model_runtime_paths.yaml"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
LABEL_EXCLUDE_NAMES = {"classes.txt", "labels.txt"}
DEFAULT_MODEL_CANDIDATE = "runs/field_multiclass/yolov8n_v1/weights/best.pt"


@dataclass(frozen=True)
class DatasetPair:
    image: Path
    label: Path


def class_order_rows() -> list[dict[str, Any]]:
    return [{"class_id": class_id, "class_name": name} for class_id, name in CLASS_ORDER.items()]


def write_class_order_config(path: Path = CLASS_ORDER_CONFIG) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "class_order:",
        "  0: struktur_penyangga",
        "  1: konduktor",
        "  2: pohon_sono",
        "aliases:",
        "  struktur_penyangga: [P001_struktur_penyangga, pole, tiang]",
        "  konduktor: [K001_konduktor, conductor, cable, kabel]",
        "  pohon_sono: [V001_pohon_sono, tree canopy, vegetation]",
        "policy:",
        "  no_fake_label: true",
        "  no_class_order_change: true",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_yolo_classes_template(path: Path = YOLO_CLASSES_TEMPLATE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(CLASS_NAMES) + "\n", encoding="utf-8")
    return path


def write_local_model_runtime_example(path: Path = LOCAL_MODEL_RUNTIME_EXAMPLE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Copy to configs/local_model_runtime_paths.yaml if an operator needs a local override.",
        "# Do not commit local_model_runtime_paths.yaml if it contains local private paths.",
        "candidate_model_paths:",
        "  - models/field/best.pt",
        "  - runs/field_multiclass/yolov8n_v1/weights/best.pt",
        "env_override: ULP_YOLO_MODEL_PATH",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def list_review_images(point_dir: Path = REVIEW_POINT_DIR) -> list[Path]:
    preferred = point_dir / "images_selected"
    fallback = point_dir / "images_all"
    image_dir = preferred if preferred.exists() else fallback
    if not image_dir.exists():
        return []
    return sorted(path for path in image_dir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def build_labeling_manifest(output: Path = LABEL_AUDIT_DIR / "labeling_manifest.csv", point_id: str = REVIEW_POINT) -> dict[str, Any]:
    images = list_review_images(DATASET_ROOT / "00_review_candidates" / point_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image_path", "image_name", "point_id", "expected_object_group", "label_status", "notes"])
        writer.writeheader()
        for image in images:
            writer.writerow(
                {
                    "image_path": _rel(image),
                    "image_name": image.name,
                    "point_id": point_id,
                    "expected_object_group": "pohon_sono_initial_focus_multiclass_context",
                    "label_status": "WAITING_FOR_MAKESENSE_LABEL",
                    "notes": "Label manually in MakeSense; do not auto-generate bounding boxes.",
                }
            )
    return {
        "status": "LABELING_MANIFEST_READY",
        "manifest_path": str(output),
        "image_count": len(images),
        "class_order": class_order_rows(),
        "no_fake_label": True,
    }


def prepare_labeling_handoff() -> dict[str, Any]:
    config = write_class_order_config()
    classes = write_yolo_classes_template()
    local_model_example = write_local_model_runtime_example()
    manifest = build_labeling_manifest()
    export_dirs = [str(path) for path in discover_export_roots() if path.exists()]
    return {
        "status": "PROGRESS_6_1_LABELING_HANDOFF_READY",
        "class_order_config": str(config),
        "classes_template": str(classes),
        "local_model_runtime_example": str(local_model_example),
        "manifest": manifest,
        "export_dirs_present": export_dirs,
        "no_fake_label": True,
    }


def discover_export_roots() -> list[Path]:
    return [
        MAKESENSE_EXPORT_DIR,
        MAKESENSE_EXPORT_DIR / REVIEW_POINT,
        LEGACY_MAKESENSE_EXPORT_DIR,
        LEGACY_MAKESENSE_EXPORT_DIR / REVIEW_POINT,
        REVIEW_POINT_DIR / "labels_selected",
    ]


def find_label_files(export_roots: list[Path] | None = None) -> list[Path]:
    roots = export_roots or discover_export_roots()
    labels: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix.lower() == ".txt" and root.name.lower() not in LABEL_EXCLUDE_NAMES:
            labels.append(root)
            continue
        for path in root.rglob("*.txt"):
            if path.name.lower() not in LABEL_EXCLUDE_NAMES:
                labels.append(path)
    return sorted(set(labels))


def find_export_images(export_roots: list[Path] | None = None) -> list[Path]:
    roots = export_roots or discover_export_roots()
    images: list[Path] = []
    for root in roots:
        if not root.exists() or root.is_file():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                images.append(path)
    review_images = list_review_images() if export_roots is None else []
    return sorted(set([*images, *review_images]))


def validate_label_export(
    export_roots: list[Path] | None = None,
    *,
    write_reports: bool = False,
    audit_dir: Path = LABEL_AUDIT_DIR,
) -> dict[str, Any]:
    labels = find_label_files(export_roots)
    images = find_export_images(export_roots)
    if not labels:
        result = _empty_validation_result(images)
        if write_reports:
            write_label_audit_reports(result, audit_dir)
        return result

    image_by_stem = {path.stem: path for path in images}
    label_by_stem = {path.stem: path for path in labels}
    class_counts = {name: 0 for name in CLASS_NAMES}
    issues: list[dict[str, Any]] = []
    review_needed: list[dict[str, Any]] = []

    for label in labels:
        if label.stem not in image_by_stem:
            issues.append(_issue(label, 0, "ORPHAN_LABEL", "No matching image stem found."))
        lines = label.read_text(encoding="utf-8", errors="replace").splitlines()
        non_empty = [line for line in lines if line.strip()]
        if not non_empty:
            issues.append(_issue(label, 0, "EMPTY_LABEL_WITHOUT_NEGATIVE_STATUS", "Empty labels need explicit operator review."))
            review_needed.append({"label_path": _rel(label), "reason": "EMPTY_LABEL"})
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            parsed = parse_yolo_label_line(line)
            if parsed["status"] != "VALID":
                issues.append(_issue(label, line_number, parsed["status"], parsed.get("detail", "")))
                review_needed.append({"label_path": _rel(label), "line": line_number, "reason": parsed["status"]})
                continue
            class_counts[CLASS_ORDER[int(parsed["class_id"])]] += 1

    missing = sorted(stem for stem in image_by_stem if stem not in label_by_stem)
    duplicates = find_duplicate_images(images)
    corrupt = [path for path in images if not image_readable(path)]
    for stem in missing:
        review_needed.append({"image_name": image_by_stem[stem].name, "reason": "MISSING_LABEL"})
    for path in duplicates:
        review_needed.append({"image_path": _rel(path), "reason": "DUPLICATE_IMAGE_HASH"})
    for path in corrupt:
        review_needed.append({"image_path": _rel(path), "reason": "CORRUPT_OR_UNREADABLE_IMAGE"})

    valid = not issues and not missing and not duplicates and not corrupt
    result = {
        "status": "LABEL_EXPORT_VALID" if valid else "LABEL_EXPORT_INVALID_REVIEW_NEEDED",
        "image_count": len(images),
        "label_file_count": len(labels),
        "class_counts": class_counts,
        "missing_label_count": len(missing),
        "orphan_label_count": sum(1 for item in issues if item["issue"] == "ORPHAN_LABEL"),
        "bad_row_count": sum(1 for item in issues if item["issue"] not in {"ORPHAN_LABEL", "EMPTY_LABEL_WITHOUT_NEGATIVE_STATUS"}),
        "empty_label_count": sum(1 for item in issues if item["issue"] == "EMPTY_LABEL_WITHOUT_NEGATIVE_STATUS"),
        "duplicate_image_count": len(duplicates),
        "corrupt_image_count": len(corrupt),
        "issues": issues,
        "review_needed": review_needed,
        "class_imbalance_status": class_imbalance_status(class_counts),
        "no_fake_label": True,
    }
    if write_reports:
        write_label_audit_reports(result, audit_dir)
    return result


def parse_yolo_label_line(line: str) -> dict[str, Any]:
    parts = line.strip().split()
    if len(parts) != 5:
        return {"status": "BAD_COLUMN_COUNT", "detail": f"expected 5 got {len(parts)}"}
    try:
        class_id = int(parts[0])
    except ValueError:
        return {"status": "BAD_CLASS_ID", "detail": parts[0]}
    if class_id not in CLASS_ORDER:
        return {"status": "CLASS_ID_OUT_OF_RANGE", "class_id": class_id}
    try:
        x_center, y_center, width, height = [float(value) for value in parts[1:]]
    except ValueError:
        return {"status": "BAD_FLOAT", "detail": " ".join(parts[1:])}
    values = [x_center, y_center, width, height]
    if not all(0.0 <= value <= 1.0 for value in values):
        return {"status": "COORDINATE_OUT_OF_RANGE", "detail": " ".join(parts[1:])}
    if width <= 0.0 or height <= 0.0:
        return {"status": "NON_POSITIVE_SIZE", "detail": f"{width} {height}"}
    return {"status": "VALID", "class_id": class_id, "bbox": values}


def write_label_audit_reports(result: dict[str, Any], audit_dir: Path = LABEL_AUDIT_DIR) -> dict[str, str]:
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / "label_audit_report.json"
    csv_path = audit_dir / "label_audit_report.csv"
    review_path = audit_dir / "review_needed.csv"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for key in ["status", "image_count", "label_file_count", "missing_label_count", "orphan_label_count", "bad_row_count", "empty_label_count", "duplicate_image_count", "corrupt_image_count", "class_imbalance_status"]:
            writer.writerow([key, result.get(key)])
        for name, count in result.get("class_counts", {}).items():
            writer.writerow([f"class_count_{name}", count])
    with review_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["image_name", "image_path", "label_path", "line", "reason"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in result.get("review_needed", []):
            writer.writerow({key: item.get(key, "") for key in fieldnames})
    return {"json": str(json_path), "csv": str(csv_path), "review_needed": str(review_path)}


def collect_dataset_pairs(export_roots: list[Path] | None = None) -> list[DatasetPair]:
    labels = find_label_files(export_roots)
    images = find_export_images(export_roots)
    image_by_stem = {path.stem: path for path in images}
    pairs: list[DatasetPair] = []
    for label in labels:
        image = image_by_stem.get(label.stem)
        if image is not None:
            pairs.append(DatasetPair(image=image, label=label))
    return sorted(pairs, key=lambda pair: pair.image.name)


def build_yolo_dataset(
    *,
    mode: str = "dry-run",
    output_dir: Path = FIELD_DATASET_DIR,
    train_ratio: float = 0.7,
    val_ratio: float = 0.2,
    test_ratio: float = 0.1,
    seed: int = SEED,
    export_roots: list[Path] | None = None,
) -> dict[str, Any]:
    validation = validate_label_export(export_roots)
    if validation["status"] != "LABEL_EXPORT_VALID":
        return {
            "status": "DATASET_BUILD_SKIPPED_LABELS_NOT_READY",
            "validation_status": validation["status"],
            "total_pairs": 0,
            "data_yaml": str(output_dir / "data.yaml"),
        }
    pairs = collect_dataset_pairs(export_roots)
    if len(pairs) < 2:
        return {
            "status": "DATASET_BUILD_SKIPPED_INSUFFICIENT_DATA",
            "validation_status": validation["status"],
            "total_pairs": len(pairs),
            "data_yaml": str(output_dir / "data.yaml"),
        }
    splits = split_dataset_pairs(pairs, train_ratio=train_ratio, val_ratio=val_ratio, test_ratio=test_ratio, seed=seed)
    split_policy = "DEFAULT_70_20_10"
    if len(pairs) < 10:
        splits = split_dataset_pairs(pairs, train_ratio=0.8, val_ratio=0.2, test_ratio=0.0, seed=seed)
        split_policy = "TEST_SPLIT_SKIPPED_SMALL_DATASET"
    if mode == "build":
        write_dataset_files(splits, output_dir)
    return {
        "status": "DATASET_BUILD_DRY_RUN_READY" if mode == "dry-run" else "DATASET_BUILD_READY",
        "validation_status": validation["status"],
        "total_pairs": len(pairs),
        "train_count": len(splits["train"]),
        "val_count": len(splits["val"]),
        "test_count": len(splits["test"]),
        "split_policy": split_policy,
        "data_yaml": str(output_dir / "data.yaml"),
        "class_counts": validation["class_counts"],
        "class_imbalance_status": validation["class_imbalance_status"],
    }


def split_dataset_pairs(
    pairs: list[DatasetPair],
    *,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[DatasetPair]]:
    if round(train_ratio + val_ratio + test_ratio, 6) != 1.0:
        raise ValueError("split ratios must sum to 1")
    shuffled = list(pairs)
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    train_count = max(1, int(total * train_ratio))
    val_count = max(1, int(total * val_ratio)) if total > 1 else 0
    if train_count + val_count > total:
        val_count = max(0, total - train_count)
    test_count = max(0, total - train_count - val_count)
    return {
        "train": shuffled[:train_count],
        "val": shuffled[train_count : train_count + val_count],
        "test": shuffled[train_count + val_count : train_count + val_count + test_count],
    }


def write_dataset_files(splits: dict[str, list[DatasetPair]], output_dir: Path = FIELD_DATASET_DIR) -> None:
    for split_name, pairs in splits.items():
        for pair in pairs:
            image_target = output_dir / "images" / split_name / pair.image.name
            label_target = output_dir / "labels" / split_name / pair.label.name
            image_target.parent.mkdir(parents=True, exist_ok=True)
            label_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pair.image, image_target)
            shutil.copy2(pair.label, label_target)
    write_data_yaml(output_dir, include_test=bool(splits.get("test")))
    write_dataset_manifest(splits, output_dir / "dataset_manifest.csv")
    report = {
        "status": "DATASET_BUILD_READY",
        "timestamp": datetime.now().isoformat(),
        "split_counts": {key: len(value) for key, value in splits.items()},
        "seed": SEED,
    }
    (output_dir / "dataset_build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_data_yaml(output_dir: Path = FIELD_DATASET_DIR, *, include_test: bool = True) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "path: data/dataset_yolo/field_multiclass_v1",
        "train: images/train",
        "val: images/val",
    ]
    if include_test:
        lines.append("test: images/test")
    lines.extend(["names:", "  0: struktur_penyangga", "  1: konduktor", "  2: pohon_sono"])
    path = output_dir / "data.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_dataset_manifest(splits: dict[str, list[DatasetPair]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["split", "image_path", "label_path"])
        for split_name, pairs in splits.items():
            for pair in pairs:
                writer.writerow([split_name, _rel(pair.image), _rel(pair.label)])


def build_training_command(
    *,
    data_yaml: Path = FIELD_DATASET_DIR / "data.yaml",
    model: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: str = "-1",
    device: str = "0",
    project: str = "runs/field_multiclass",
    name: str = "yolov8n_v1",
) -> list[str]:
    return [
        ".\\venv\\Scripts\\yolo.exe",
        "detect",
        "train",
        f"model={model}",
        f"data={data_yaml.as_posix()}",
        f"epochs={epochs}",
        f"imgsz={imgsz}",
        f"batch={batch}",
        f"device={device}",
        f"project={project}",
        f"name={name}",
        f"seed={SEED}",
        "patience=15",
    ]


def training_plan(*, data_yaml: Path = FIELD_DATASET_DIR / "data.yaml", cuda_available: bool | None = None) -> dict[str, Any]:
    if not data_yaml.exists():
        return {
            "status": "TRAINING_NOT_RUN_DATASET_NOT_READY",
            "command": " ".join(build_training_command(data_yaml=data_yaml)),
            "no_fake_accuracy": True,
        }
    if cuda_available is False:
        command = build_training_command(data_yaml=data_yaml, epochs=3, batch="auto", device="cpu", name="yolov8n_v1_cpu_smoke")
        return {"status": "TRAINING_SMOKE_CPU_ONLY", "command": " ".join(command), "no_fake_accuracy": True}
    command = build_training_command(data_yaml=data_yaml)
    return {"status": "TRAINING_COMMAND_READY_NOT_RUN_BY_DEFAULT", "command": " ".join(command), "no_fake_accuracy": True}


def check_trained_model(model_path: Path) -> dict[str, Any]:
    if not model_path.exists():
        return {"status": "BESTPT_NOT_FOUND", "model_path": str(model_path), "runtime_integration": "MODEL_NOT_READY"}
    if model_path.suffix.lower() not in {".pt", ".onnx"}:
        return {"status": "BESTPT_INVALID_SUFFIX", "model_path": str(model_path), "runtime_integration": "MODEL_NOT_READY"}
    if model_path.stat().st_size < 1024:
        return {"status": "BESTPT_INVALID_SIZE", "model_path": str(model_path), "runtime_integration": "MODEL_NOT_READY"}
    handoff = check_model_handoff(model_path)
    return {
        "status": "MODEL_LOAD_CANDIDATE_READY_CLASS_ORDER_UNVERIFIED"
        if handoff["model_status"] == "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED"
        else handoff["model_status"],
        "model_path": str(model_path),
        "class_order_status": handoff.get("class_order_status", "CLASS_ORDER_UNVERIFIED"),
        "runtime_integration": "REAL_MODEL_CANDIDATE_READY" if handoff["model_status"].startswith("MODEL_PRESENT") else "MODEL_NOT_READY",
        "not_accuracy_claim": True,
    }


def integrate_bestpt_runtime(model_path: Path = PROJECT_ROOT / DEFAULT_MODEL_CANDIDATE) -> dict[str, Any]:
    config_text = MODEL_RUNTIME_CONFIG.read_text(encoding="utf-8") if MODEL_RUNTIME_CONFIG.exists() else ""
    registered = DEFAULT_MODEL_CANDIDATE in config_text or str(model_path).replace("\\", "/") in config_text
    model = check_trained_model(model_path)
    return {
        "status": "BESTPT_RUNTIME_PATH_REGISTERED" if registered else "BESTPT_RUNTIME_PATH_NOT_REGISTERED",
        "candidate_path": str(model_path),
        "model_status": model["status"],
        "runtime_integration": model["runtime_integration"],
        "do_not_commit_weights": True,
    }


def progress6_1_gate_status() -> dict[str, Any]:
    handoff = prepare_labeling_handoff()
    validation = validate_label_export(write_reports=False)
    dataset = build_yolo_dataset(mode="dry-run")
    training = training_plan()
    bestpt = integrate_bestpt_runtime()
    if validation["status"] == "MAKESENSE_EXPORT_NOT_FOUND":
        status = "PROGRESS_6_1_LABELING_HANDOFF_READY_WAITING_FOR_MAKESENSE_EXPORT"
    elif validation["status"] != "LABEL_EXPORT_VALID":
        status = "PROGRESS_6_1_LABEL_AUDIT_READY_INSUFFICIENT_DATA_FOR_TRAINING"
    elif dataset["status"] in {"DATASET_BUILD_DRY_RUN_READY", "DATASET_BUILD_READY"}:
        status = "PROGRESS_6_1_INITIAL_YOLO_TRAINING_PIPELINE_READY"
    else:
        status = "PROGRESS_6_1_LABEL_AUDIT_READY_INSUFFICIENT_DATA_FOR_TRAINING"
    if bestpt["runtime_integration"] == "REAL_MODEL_CANDIDATE_READY":
        status = "PROGRESS_6_1_BESTPT_INTEGRATED_RUNTIME_REAL_MODEL_READY"
    return {
        "status": status,
        "handoff": handoff,
        "validation": validation,
        "dataset": dataset,
        "training": training,
        "bestpt": bestpt,
        "class_order_status": "CLASS_ORDER_LOCKED",
        "no_fake_label": True,
        "no_fake_detection": True,
    }


def class_imbalance_status(class_counts: dict[str, int]) -> str:
    if not any(class_counts.values()):
        return "CLASS_IMBALANCE_EXPECTED_INITIAL_TREE_FOCUS"
    if any(class_counts.get(name, 0) == 0 for name in CLASS_NAMES):
        return "CLASS_IMBALANCE_EXPECTED_INITIAL_TREE_FOCUS"
    counts = [class_counts[name] for name in CLASS_NAMES]
    if max(counts) > min(counts) * 3:
        return "CLASS_IMBALANCE_REVIEW_RECOMMENDED"
    return "CLASS_BALANCE_ACCEPTABLE_FOR_INITIAL_TRAINING"


def image_readable(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
        return bool(head)
    except OSError:
        return False


def find_duplicate_images(images: list[Path]) -> list[Path]:
    seen: dict[str, Path] = {}
    duplicates: list[Path] = []
    for path in images:
        digest = _sha1(path)
        if not digest:
            continue
        if digest in seen:
            duplicates.append(path)
        else:
            seen[digest] = path
    return duplicates


def _sha1(path: Path) -> str:
    try:
        digest = hashlib.sha1()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return ""


def _empty_validation_result(images: list[Path]) -> dict[str, Any]:
    return {
        "status": "MAKESENSE_EXPORT_NOT_FOUND",
        "image_count": len(images),
        "label_file_count": 0,
        "class_counts": {name: 0 for name in CLASS_NAMES},
        "missing_label_count": len(images),
        "orphan_label_count": 0,
        "bad_row_count": 0,
        "empty_label_count": 0,
        "duplicate_image_count": 0,
        "corrupt_image_count": 0,
        "issues": [],
        "review_needed": [{"image_name": path.name, "reason": "WAITING_FOR_MAKESENSE_EXPORT"} for path in images],
        "class_imbalance_status": "CLASS_IMBALANCE_EXPECTED_INITIAL_TREE_FOCUS",
        "no_fake_label": True,
    }


def _issue(path: Path, line: int, issue: str, detail: str) -> dict[str, Any]:
    return {"file": _rel(path), "line": line, "issue": issue, "detail": detail}


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
