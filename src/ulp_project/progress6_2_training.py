"""Progress 6.2 MakeSense export to YOLO training handoff helpers."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from .classes import CLASS_NAMES
from .paths import PROJECT_ROOT
from .progress6_1_labeling import (
    FIELD_DATASET_DIR,
    LABEL_AUDIT_DIR,
    MAKESENSE_EXPORT_DIR,
    SEED,
    build_yolo_dataset,
    check_trained_model,
    collect_dataset_pairs,
    integrate_bestpt_runtime,
    training_plan,
    validate_label_export,
)

PROGRESS6_2_ALLOWED_STATUSES = {
    "PROGRESS_6_2_BLOCKED_MAKESENSE_EXPORT_NOT_FOUND",
    "PROGRESS_6_2_LABEL_EXPORT_INVALID_REVIEW_REQUIRED",
    "PROGRESS_6_2_LABEL_EXPORT_VALID_READY_FOR_DATASET_BUILD",
    "PROGRESS_6_2_DATASET_BUILD_READY_TRAINING_NOT_RUN",
    "PROGRESS_6_2_TRAINING_SMOKE_COMPLETE_NOT_FINAL_MODEL",
    "PROGRESS_6_2_BESTPT_VALID_RUNTIME_REAL_MODEL_READY",
}


def extract_makesense_zips(export_dir: Path = MAKESENSE_EXPORT_DIR) -> dict[str, Any]:
    """Extract MakeSense zip files into an ignored working directory."""
    if not export_dir.exists():
        return {"status": "MAKESENSE_EXPORT_DIR_NOT_FOUND", "zip_count": 0, "extracted_roots": []}
    zip_files = sorted(path for path in export_dir.glob("*.zip") if path.is_file())
    extracted_roots: list[str] = []
    extracted_base = export_dir / "extracted"
    for zip_path in zip_files:
        target_dir = extracted_base / zip_path.stem
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                target = (target_dir / member.filename).resolve()
                if not target.is_relative_to(target_dir.resolve()):
                    raise ValueError(f"Unsafe zip member path: {member.filename}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as destination:
                    destination.write(source.read())
        extracted_roots.append(str(target_dir))
    status = "MAKESENSE_ZIP_EXTRACTED" if zip_files else "NO_ZIP_EXPORT_FOUND"
    return {"status": status, "zip_count": len(zip_files), "extracted_roots": extracted_roots}


def validate_export_class_order(export_roots: list[Path] | None = None) -> dict[str, Any]:
    roots = export_roots or [MAKESENSE_EXPORT_DIR]
    class_files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.name.lower() in {"classes.txt", "labels.txt"}:
            class_files.append(root)
            continue
        for name in ("classes.txt", "labels.txt"):
            class_files.extend(sorted(path for path in root.rglob(name) if path.is_file()))
    if not class_files:
        return {
            "status": "CLASS_ORDER_FROM_CONFIG_NO_EXPORT_CLASS_FILE",
            "expected": CLASS_NAMES,
            "class_files": [],
            "class_order_ok": True,
        }
    checked: list[dict[str, Any]] = []
    ok = True
    for path in sorted(set(class_files)):
        names = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        matches = names[: len(CLASS_NAMES)] == CLASS_NAMES
        ok = ok and matches
        checked.append({"path": _rel(path), "names": names, "matches_expected_order": matches})
    return {
        "status": "CLASS_ORDER_OK" if ok else "CLASS_ORDER_INVALID_REVIEW_REQUIRED",
        "expected": CLASS_NAMES,
        "class_files": checked,
        "class_order_ok": ok,
    }


def progress6_2_export_audit(
    export_roots: list[Path] | None = None,
    *,
    write_reports: bool = False,
    extract_zips: bool = True,
) -> dict[str, Any]:
    extraction = extract_makesense_zips() if extract_zips and export_roots is None else {"status": "ZIP_EXTRACTION_SKIPPED", "zip_count": 0, "extracted_roots": []}
    roots = export_roots
    class_order = validate_export_class_order(roots)
    validation = validate_label_export(roots, write_reports=write_reports, audit_dir=LABEL_AUDIT_DIR)
    pairs = collect_dataset_pairs(roots) if validation["status"] == "LABEL_EXPORT_VALID" else []
    bbox_total = int(validation.get("bbox_total", sum(validation.get("class_counts", {}).values())))
    review_needed_count = len(validation.get("review_needed", []))
    invalid_count = len(validation.get("issues", []))
    if validation["status"] == "MAKESENSE_EXPORT_NOT_FOUND":
        status = "PROGRESS_6_2_BLOCKED_MAKESENSE_EXPORT_NOT_FOUND"
    elif not class_order["class_order_ok"] or validation["status"] != "LABEL_EXPORT_VALID":
        status = "PROGRESS_6_2_LABEL_EXPORT_INVALID_REVIEW_REQUIRED"
    elif len(pairs) < 2:
        status = "PROGRESS_6_2_LABEL_EXPORT_VALID_INSUFFICIENT_DATA_FOR_REAL_TRAINING"
    else:
        status = "PROGRESS_6_2_LABEL_EXPORT_VALID_READY_FOR_DATASET_BUILD"
    return {
        "status": status,
        "extraction": extraction,
        "class_order": class_order,
        "validation": validation,
        "image_count": validation.get("image_count", 0),
        "label_file_count": validation.get("label_file_count", 0),
        "bbox_total": bbox_total,
        "class_counts": validation.get("class_counts", {name: 0 for name in CLASS_NAMES}),
        "label_invalid_count": invalid_count,
        "review_needed_count": review_needed_count,
        "dataset_pair_count": len(pairs),
        "class_imbalance_status": validation.get("class_imbalance_status"),
        "no_fake_label": True,
    }


def progress6_2_dataset_build_status(
    *,
    mode: str = "dry-run",
    export_roots: list[Path] | None = None,
    output_dir: Path = FIELD_DATASET_DIR,
) -> dict[str, Any]:
    audit = progress6_2_export_audit(export_roots, write_reports=False, extract_zips=export_roots is None)
    if audit["status"] not in {
        "PROGRESS_6_2_LABEL_EXPORT_VALID_READY_FOR_DATASET_BUILD",
        "PROGRESS_6_2_LABEL_EXPORT_VALID_INSUFFICIENT_DATA_FOR_REAL_TRAINING",
    }:
        return {
            "status": "DATASET_BUILD_SKIPPED_LABELS_NOT_READY",
            "progress6_2_status": audit["status"],
            "data_yaml": str(output_dir / "data.yaml"),
            "train_count": 0,
            "val_count": 0,
            "test_count": 0,
        }
    dataset = build_yolo_dataset(mode=mode, export_roots=export_roots, output_dir=output_dir)
    return dataset


def cuda_status() -> dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local env
        return {"status": "TORCH_NOT_AVAILABLE", "cuda_available": False, "device": "CPU", "detail": str(exc)}
    available = bool(torch.cuda.is_available())
    return {
        "status": "CUDA_AVAILABLE" if available else "CPU_ONLY",
        "cuda_available": available,
        "device": torch.cuda.get_device_name(0) if available else "CPU",
    }


def progress6_2_training_policy_status(data_yaml: Path = FIELD_DATASET_DIR / "data.yaml") -> dict[str, Any]:
    cuda = cuda_status()
    plan = training_plan(data_yaml=data_yaml, cuda_available=cuda["cuda_available"])
    if plan["status"] == "TRAINING_NOT_RUN_DATASET_NOT_READY":
        progress_status = "TRAINING_NOT_RUN_DATASET_NOT_READY"
    elif plan["status"] == "TRAINING_SMOKE_CPU_ONLY":
        progress_status = "TRAINING_SMOKE_CPU_ONLY"
    else:
        progress_status = "TRAINING_COMMAND_READY_NOT_RUN_BY_DEFAULT"
    return {
        "status": progress_status,
        "cuda": cuda,
        "plan": plan,
        "training_executed": False,
        "no_fake_accuracy": True,
    }


def progress6_2_bestpt_handoff_status(model_path: Path | None = None) -> dict[str, Any]:
    candidate = model_path or PROJECT_ROOT / "runs" / "field_multiclass" / "yolov8n_v1" / "weights" / "best.pt"
    model = check_trained_model(candidate)
    runtime = integrate_bestpt_runtime(candidate)
    status = "BESTPT_VALID_RUNTIME_REAL_MODEL_READY" if model.get("runtime_integration") == "REAL_MODEL_CANDIDATE_READY" else "BESTPT_NOT_READY_MODEL_NOT_READY_SAFE_MODE"
    return {"status": status, "model": model, "runtime": runtime, "no_fake_detection": True}


def progress6_2_gate_status(*, write_reports: bool = False) -> dict[str, Any]:
    audit = progress6_2_export_audit(write_reports=write_reports)
    dataset = progress6_2_dataset_build_status(mode="dry-run")
    training = progress6_2_training_policy_status()
    bestpt = progress6_2_bestpt_handoff_status()
    if bestpt["status"] == "BESTPT_VALID_RUNTIME_REAL_MODEL_READY":
        status = "PROGRESS_6_2_BESTPT_VALID_RUNTIME_REAL_MODEL_READY"
    elif audit["status"] == "PROGRESS_6_2_BLOCKED_MAKESENSE_EXPORT_NOT_FOUND":
        status = audit["status"]
    elif audit["status"] == "PROGRESS_6_2_LABEL_EXPORT_INVALID_REVIEW_REQUIRED":
        status = audit["status"]
    elif dataset["status"] in {"DATASET_BUILD_DRY_RUN_READY", "DATASET_BUILD_READY"}:
        status = "PROGRESS_6_2_LABEL_EXPORT_VALID_READY_FOR_DATASET_BUILD"
    else:
        status = audit["status"]
    return {
        "status": status,
        "audit": audit,
        "dataset": dataset,
        "training": training,
        "bestpt": bestpt,
        "seed": SEED,
        "no_fake_label": True,
        "no_fake_detection": True,
        "no_dataset_botol": True,
        "no_runtime_regression": True,
    }


def write_progress6_2_report(path: Path, result: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
