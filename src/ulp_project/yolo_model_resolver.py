"""Resolve custom YOLO model path without downloading or training."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "yolo_runtime.yaml"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "field" / "best.pt"


def load_yolo_runtime_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve_yolo_model(config_path: Path = DEFAULT_CONFIG_PATH, env_var: str = "ULP_YOLO_MODEL_PATH") -> dict[str, Any]:
    config = load_yolo_runtime_config(config_path)
    configured = os.environ.get(env_var) or config.get("model_path") or str(DEFAULT_MODEL_PATH)
    path = Path(configured)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    runtime = {
        "device": config.get("device", "auto"),
        "conf_threshold": config.get("conf_threshold", 0.25),
        "iou_threshold": config.get("iou_threshold", 0.5),
        "max_detections": config.get("max_detections", 100),
        "image_size": config.get("image_size", 640),
    }
    if not path.exists():
        return {
            "status": "MODEL_NOT_READY",
            "model_path": str(path),
            "runtime": runtime,
            "reason": "Custom YOLO model is not available yet. No download or training is attempted.",
            "not_accuracy_claim": True,
        }
    return {
        "status": "MODEL_READY_UNVALIDATED",
        "model_path": str(path),
        "runtime": runtime,
        "reason": "Model file exists, but accuracy still requires project validation.",
        "not_accuracy_claim": True,
    }


def normalize_yolo_class_name(label: str, config_path: Path = DEFAULT_CONFIG_PATH) -> str:
    raw = (label or "").strip()
    lowered = raw.lower()
    config = load_yolo_runtime_config(config_path)
    classes = config.get("allowed_classes", {})
    for canonical, details in classes.items():
        aliases = [canonical, *(details.get("aliases", []) if isinstance(details, dict) else [])]
        if lowered in {str(alias).lower() for alias in aliases}:
            return canonical
    if "_struktur_penyangga" in lowered or lowered.startswith("p") and "struktur" in lowered:
        return "struktur_penyangga"
    if "_konduktor" in lowered or lowered.startswith("k") and "konduktor" in lowered:
        return "konduktor"
    if "_pohon_sono" in lowered or lowered.startswith("v") and "pohon_sono" in lowered:
        return "pohon_sono"
    return raw
