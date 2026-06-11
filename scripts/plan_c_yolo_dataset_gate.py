from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_feedback_learning import ACCEPTED_JSONL  # noqa: E402

TARGET_ROOT = ROOT / "data" / "training_gate" / "plan_c_yolo_vegetation"
REVIEW_QUEUE = TARGET_ROOT / "review_queue"
REPORT_PATH = TARGET_ROOT / "gate_report.json"
REVIEW_MANIFEST = REVIEW_QUEUE / "accepted_feedback_manifest.jsonl"
DATASET_YAML = TARGET_ROOT / "dataset.yaml"

CLASS_NAMES = ["struktur_penyangga", "konduktor", "pohon_sono", "pohon_non_sono"]
MIN_IMAGES_PER_CLASS = 20
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def main() -> int:
    report = run_gate()
    print(report["status"])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def run_gate() -> dict[str, Any]:
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    REVIEW_QUEUE.mkdir(parents=True, exist_ok=True)

    accepted = _load_accepted_feedback()
    review_export = _write_review_manifest(accepted)
    local_scan = _scan_local_candidates()
    dataset_status = _validate_dataset_layout(TARGET_ROOT)

    if dataset_status["ready"]:
        _write_dataset_yaml()
        status = "YOLO_TRAINING_DATA_READY"
        training_status = "YOLO_TRAINING_SKIPPED_SAFE"
    else:
        status = "YOLO_TRAINING_DATA_NOT_ENOUGH"
        training_status = "YOLO_TRAINING_SKIPPED_SAFE"

    report = {
        "ok": True,
        "status": status,
        "training_status": training_status,
        "class_order": {str(index): name for index, name in enumerate(CLASS_NAMES)},
        "min_images_per_class": MIN_IMAGES_PER_CLASS,
        "accepted_feedback_records": len(accepted),
        "review_export": review_export,
        "local_scan": local_scan,
        "dataset_validation": dataset_status,
        "dataset_yaml": str(DATASET_YAML.relative_to(ROOT)) if DATASET_YAML.exists() else "",
        "dataset_yaml_current_run_created": dataset_status["ready"],
        "no_training_started": True,
        "no_internet_download": True,
        "notes": [
            "Feedback accepted masuk review_queue, bukan dataset training resmi.",
            "Raw image baru dan model hasil training tidak dibuat atau di-commit oleh gate ini.",
            "Jika dataset internet dibutuhkan, sumber dan izin harus diverifikasi manual lebih dulu.",
        ],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _load_accepted_feedback() -> list[dict[str, Any]]:
    if not ACCEPTED_JSONL.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in ACCEPTED_JSONL.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def _write_review_manifest(records: list[dict[str, Any]]) -> dict[str, Any]:
    REVIEW_QUEUE.mkdir(parents=True, exist_ok=True)
    written = 0
    with REVIEW_MANIFEST.open("w", encoding="utf-8") as handle:
        for item in records:
            session_id = str(item.get("session_id") or "").strip()
            if not session_id:
                continue
            manifest = {
                "session_id": session_id,
                "original_path": _relative_or_empty(item.get("original_path")),
                "annotated_path": _relative_or_empty(item.get("annotated_path")),
                "label_path": _relative_or_empty(item.get("label_path")),
                "species_status": item.get("species_status"),
                "zone_status": item.get("zone_status"),
                "risk_status": item.get("risk_status"),
                "prediction_window": item.get("prediction_window"),
                "review_only": True,
            }
            handle.write(json.dumps(manifest, ensure_ascii=False) + "\n")
            written += 1
    return {
        "status": "PLAN_C_FEEDBACK_REVIEW_QUEUE_READY",
        "manifest": str(REVIEW_MANIFEST.relative_to(ROOT)),
        "records_written": written,
    }


def _scan_local_candidates() -> dict[str, Any]:
    roots = [
        ROOT / "data" / "dataset_yolo",
        ROOT / "data" / "reference",
        ROOT / "data" / "training_gate",
        ROOT / "data" / "runtime" / "plan_c" / "feedback",
    ]
    summary: dict[str, Any] = {"roots": []}
    for root in roots:
        item = {"path": str(root.relative_to(ROOT)), "exists": root.exists(), "images": 0, "labels": 0}
        if root.exists():
            item["images"] = _count_files(root, IMAGE_EXTENSIONS)
            item["labels"] = _count_files(root, {".txt"})
        summary["roots"].append(item)
    return summary


def _validate_dataset_layout(root: Path) -> dict[str, Any]:
    train_images = root / "images" / "train"
    val_images = root / "images" / "val"
    train_labels = root / "labels" / "train"
    val_labels = root / "labels" / "val"
    missing = [str(path.relative_to(ROOT)) for path in [train_images, val_images, train_labels, val_labels] if not path.exists()]
    if missing:
        return {"ready": False, "reason": "DATASET_LAYOUT_MISSING", "missing": missing}

    train_image_count = _count_files(train_images, IMAGE_EXTENSIONS)
    val_image_count = _count_files(val_images, IMAGE_EXTENSIONS)
    train_label_count = _count_files(train_labels, {".txt"})
    val_label_count = _count_files(val_labels, {".txt"})
    class_counts = _class_counts([train_labels, val_labels])
    classes_ready = all(class_counts.get(str(index), 0) >= MIN_IMAGES_PER_CLASS for index in range(len(CLASS_NAMES)))
    ready = train_image_count > 0 and val_image_count > 0 and train_label_count > 0 and val_label_count > 0 and classes_ready
    return {
        "ready": ready,
        "reason": "DATASET_READY" if ready else "CLASS_OR_SPLIT_COUNT_NOT_ENOUGH",
        "images_train": train_image_count,
        "images_val": val_image_count,
        "labels_train": train_label_count,
        "labels_val": val_label_count,
        "class_counts": class_counts,
    }


def _write_dataset_yaml() -> None:
    lines = [
        f"path: {TARGET_ROOT.as_posix()}",
        "train: images/train",
        "val: images/val",
        "names:",
    ]
    lines.extend(f"  {index}: {name}" for index, name in enumerate(CLASS_NAMES))
    DATASET_YAML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _class_counts(label_roots: list[Path]) -> dict[str, int]:
    counts = {str(index): 0 for index in range(len(CLASS_NAMES))}
    for root in label_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.txt"):
            for row in _label_rows(path):
                class_id = row[0] if row else ""
                if class_id in counts:
                    counts[class_id] += 1
    return counts


def _label_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            for row in csv.reader(handle, delimiter=" "):
                values = [value for value in row if value != ""]
                if values:
                    rows.append(values)
    except OSError:
        return []
    return rows


def _count_files(root: Path, extensions: set[str]) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in extensions)


def _relative_or_empty(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        path = Path(text)
        if path.is_absolute():
            return str(path.relative_to(ROOT))
    except ValueError:
        return ""
    return text.replace("\\", "/")


if __name__ == "__main__":
    raise SystemExit(main())
