"""Progress status consistency checks for model handoff messaging."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .classes import CLASS_ORDER
from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT
from .progress6_1_labeling import MAKESENSE_EXPORT_DIR, FIELD_DATASET_DIR, progress6_1_gate_status


def build_status_consistency_audit(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    progress6_1 = progress6_1_gate_status()
    handoff = check_model_handoff(dry_load=False)
    bestpt = root / "runs" / "field_multiclass" / "yolov8n_v1" / "weights" / "best.pt"
    data_yaml = FIELD_DATASET_DIR / "data.yaml"

    runtime_model_status = str(handoff.get("model_status") or "MODEL_NOT_READY")
    progress5_4_status = (
        "PROGRESS_5_4_REMOTE_HTTPS_CAMERA_GPS_YOLO_SHUTTER_READY_WITH_REAL_MODEL"
        if runtime_model_status not in {"MODEL_NOT_READY"}
        else "PROGRESS_5_4_REMOTE_HTTPS_CAMERA_GPS_YOLO_SHUTTER_READY_MODEL_NOT_READY_SAFE_MODE"
    )
    label_export_status = _label_export_status()
    dataset_yaml_status = "DATA_YAML_PRESENT" if data_yaml.exists() else "DATA_YAML_NOT_FOUND"
    bestpt_status = _bestpt_status(bestpt, runtime_model_status)
    progress6_1_status = str(progress6_1.get("status"))
    consistency = _consistency_status(progress6_1_status, dataset_yaml_status, bestpt_status, runtime_model_status)
    operator_message, allowed_next_action = _operator_message(consistency)

    precise_6_1 = progress6_1_status
    if progress6_1_status == "PROGRESS_6_1_INITIAL_YOLO_TRAINING_PIPELINE_READY" and runtime_model_status == "MODEL_NOT_READY":
        precise_6_1 = "PROGRESS_6_1_INITIAL_TRAINING_PIPELINE_READY_MODEL_NOT_READY"

    return {
        "progress_5_4_status": progress5_4_status,
        "progress_6_1_status": progress6_1_status,
        "progress_6_1_precise_status": precise_6_1,
        "label_export_status": label_export_status,
        "dataset_yaml_status": dataset_yaml_status,
        "bestpt_status": bestpt_status,
        "runtime_model_status": runtime_model_status,
        "model_path": handoff.get("model_path", ""),
        "class_order_status": "CLASS_ORDER_LOCKED" if CLASS_ORDER == {0: "struktur_penyangga", 1: "konduktor", 2: "pohon_sono"} else "CLASS_ORDER_CHANGED",
        "status_consistency": consistency,
        "operator_message": operator_message,
        "allowed_next_action": allowed_next_action,
        "no_fake_detection": True,
        "not_accuracy_claim": True,
    }


def _label_export_status() -> str:
    if not MAKESENSE_EXPORT_DIR.exists():
        return "MAKESENSE_EXPORT_DIR_NOT_FOUND"
    labels = [path for path in MAKESENSE_EXPORT_DIR.rglob("*.txt") if path.name.lower() not in {"classes.txt", "labels.txt"}]
    images = [path for path in MAKESENSE_EXPORT_DIR.rglob("*") if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    if labels:
        return "MAKESENSE_YOLO_LABELS_PRESENT"
    if images:
        return "MAKESENSE_IMAGES_PRESENT_LABELS_NOT_FOUND"
    return "MAKESENSE_EXPORT_EMPTY_OR_WAITING"


def _bestpt_status(bestpt: Path, runtime_model_status: str) -> str:
    if not bestpt.exists():
        return "BESTPT_NOT_FOUND"
    if runtime_model_status == "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED":
        return "BESTPT_PRESENT_CLASS_ORDER_NOT_VERIFIED"
    if runtime_model_status == "REAL_MODEL":
        return "BESTPT_VALID_RUNTIME_REAL_MODEL"
    return runtime_model_status


def _consistency_status(progress6_1_status: str, dataset_yaml_status: str, bestpt_status: str, runtime_model_status: str) -> str:
    if runtime_model_status == "REAL_MODEL":
        return "REAL_MODEL_HANDOFF_READY"
    if bestpt_status == "BESTPT_PRESENT_CLASS_ORDER_NOT_VERIFIED":
        return "BESTPT_PRESENT_CLASS_ORDER_NOT_VERIFIED"
    if dataset_yaml_status == "DATA_YAML_PRESENT" and bestpt_status == "BESTPT_NOT_FOUND":
        return "DATASET_PIPELINE_READY_TRAINING_OUTPUT_NOT_FOUND"
    if "TRAINING_PIPELINE_READY" in progress6_1_status and bestpt_status == "BESTPT_NOT_FOUND":
        return "PIPELINE_READY_BUT_REAL_MODEL_NOT_AVAILABLE"
    return "MODEL_NOT_READY_STATUS_CONSISTENT"


def _operator_message(consistency: str) -> tuple[str, str]:
    if consistency == "REAL_MODEL_HANDOFF_READY":
        return "Custom YOLO valid terbaca runtime.", "Lanjut uji deteksi REAL_MODEL di HP."
    if consistency == "BESTPT_PRESENT_CLASS_ORDER_NOT_VERIFIED":
        return "best.pt ada, tetapi class order belum terverifikasi.", "Validasi best.pt sebelum mengaktifkan REAL_MODEL."
    if consistency == "DATASET_PIPELINE_READY_TRAINING_OUTPUT_NOT_FOUND":
        return "Dataset/data.yaml siap, tetapi output training best.pt belum ada.", "Jalankan training hanya setelah label valid dan instruksi training eksplisit."
    if consistency == "PIPELINE_READY_BUT_REAL_MODEL_NOT_AVAILABLE":
        return "Training pipeline/code siap, tetapi custom YOLO belum menjadi REAL_MODEL.", "Lanjut labeling/training sampai best.pt valid tersedia."
    return "Status aman: runtime tetap MODEL_NOT_READY tanpa deteksi palsu.", "Lanjut labeling atau uji HP fisik tanpa klaim model custom."
