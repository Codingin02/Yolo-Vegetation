"""Model handoff bridge for plugging in a future trained YOLO model."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "configs" / "model_runtime_paths.yaml"
LOCKED_CLASS_ORDER = {0: "struktur_penyangga", 1: "konduktor", 2: "pohon_sono"}


def load_model_handoff_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    default = {
        "candidate_model_paths": [
            "weights/best.pt",
            "models/best.pt",
            "models/field/best.pt",
            "runs/field_multiclass/yolov8n_v1/weights/best.pt",
            "runs/detect/train/weights/best.pt",
        ],
        "env_override": "ULP_YOLO_MODEL_PATH",
        "accepted_suffixes": [".pt", ".onnx"],
        "minimum_size_bytes": 1024,
        "class_order": LOCKED_CLASS_ORDER,
    }
    if not path.exists():
        return default
    try:
        import yaml
    except ImportError:
        return default
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {**default, **loaded}


def resolve_candidate_model_path(model_path: str | Path | None = None, config: dict[str, Any] | None = None) -> Path | None:
    config = config or load_model_handoff_config()
    candidates: list[str | Path] = []
    if model_path:
        candidates.append(model_path)
    env_path = os.environ.get(str(config.get("env_override", "ULP_YOLO_MODEL_PATH")))
    if env_path:
        candidates.append(env_path)
    candidates.extend(config.get("candidate_model_paths", []))
    for item in candidates:
        path = Path(item)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if path.exists():
            return path
    return None


def check_model_handoff(model_path: str | Path | None = None, *, dry_load: bool = False) -> dict[str, Any]:
    config = load_model_handoff_config()
    path = resolve_candidate_model_path(model_path, config)
    if path is None:
        return {
            "model_status": "MODEL_NOT_READY",
            "inference_status": "SKIPPED_NO_MODEL",
            "model_path": "",
            "class_order_status": "CLASS_ORDER_NOT_VERIFIED",
            "locked_class_order": LOCKED_CLASS_ORDER,
            "not_accuracy_claim": True,
        }
    suffix_ok = path.suffix.lower() in set(config.get("accepted_suffixes", [".pt", ".onnx"]))
    readable = _is_readable(path)
    size = path.stat().st_size if readable else 0
    size_ok = size >= int(config.get("minimum_size_bytes", 1024))
    if not suffix_ok:
        status = "MODEL_REJECTED_UNSUPPORTED_SUFFIX"
    elif not readable:
        status = "MODEL_REJECTED_NOT_READABLE"
    elif not size_ok:
        status = "MODEL_REJECTED_SIZE_TOO_SMALL"
    else:
        status = "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED"
    dry_load_result = _dry_load(path) if dry_load and status == "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED" else {"status": "DRY_LOAD_SKIPPED"}
    return {
        "model_status": status,
        "inference_status": "READY_DRY_LOAD_OPTIONAL" if status == "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED" else "SKIPPED_MODEL_NOT_ACCEPTED",
        "model_path": str(path),
        "suffix_ok": suffix_ok,
        "readable": readable,
        "size_bytes": size,
        "size_ok": size_ok,
        "class_order_status": "CLASS_ORDER_UNVERIFIED",
        "locked_class_order": LOCKED_CLASS_ORDER,
        "dry_load": dry_load_result,
        "not_accuracy_claim": True,
    }


def verify_model_class_order(model_names: dict[int, str] | list[str] | None) -> dict[str, Any]:
    if not model_names:
        return {"status": "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED", "locked_class_order": LOCKED_CLASS_ORDER}
    observed = {idx: name for idx, name in enumerate(model_names)} if isinstance(model_names, list) else {int(k): v for k, v in model_names.items()}
    if observed == LOCKED_CLASS_ORDER:
        return {"status": "MODEL_CLASS_ORDER_MATCH", "observed": observed}
    return {"status": "MODEL_REJECTED_CLASS_ORDER_MISMATCH", "observed": observed, "expected": LOCKED_CLASS_ORDER}


def _is_readable(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            handle.read(1)
        return True
    except OSError:
        return False


def _dry_load(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".pt":
        return {"status": "DRY_LOAD_SKIPPED_NON_PT"}
    try:
        from ultralytics import YOLO
    except ImportError:
        return {"status": "ULTRALYTICS_NOT_INSTALLED"}
    try:
        model = YOLO(str(path))
        return {"status": "DRY_LOAD_OK_CLASS_ORDER_UNVERIFIED", "names": getattr(model, "names", None)}
    except Exception as exc:  # pragma: no cover - depends on external model file
        return {"status": "DRY_LOAD_FAILED", "error": str(exc)[:200]}
