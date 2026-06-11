"""Model registry helpers for System C final runtime selection."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

MODEL_REGISTRY_PATH = PROJECT_ROOT / "data" / "model_registry" / "plan_c_model_registry.json"
CLASS_ORDER = ["struktur_penyangga", "konduktor", "pohon_sono", "pohon_non_sono"]


def register_model_if_valid(*, model_path: str | Path, dataset_version: str = "plan_c_final_v1", metrics: dict[str, Any] | None = None, gate_status: str = "") -> dict[str, Any]:
    path = Path(model_path)
    if not path.exists() or path.suffix.lower() != ".pt":
        return {"status": "MODEL_REGISTRY_SKIPPED_MODEL_FILE_NOT_VALID", "runtime_allowed": False}
    if gate_status and gate_status != "YOLO_TRAINING_READY":
        return {"status": "MODEL_REGISTRY_SKIPPED_GATE_NOT_READY", "runtime_allowed": False}
    payload = {
        "model_path": str(path),
        "model_name": path.name,
        "dataset_version": dataset_version,
        "classes": CLASS_ORDER,
        "metrics": metrics or {},
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "gate_status": gate_status or "YOLO_TRAINING_READY",
        "runtime_allowed": True,
        "notes": "Registered only after model file and gate are valid.",
    }
    MODEL_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_REGISTRY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": "MODEL_REGISTRY_UPDATED", "runtime_allowed": True, "registry_path": str(MODEL_REGISTRY_PATH)}


def load_model_registry() -> dict[str, Any]:
    if not MODEL_REGISTRY_PATH.exists():
        return {"status": "MODEL_REGISTRY_MISSING", "runtime_allowed": False}
    try:
        data = json.loads(MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "MODEL_REGISTRY_INVALID_JSON", "runtime_allowed": False}
    if data.get("classes") != CLASS_ORDER:
        return {"status": "MODEL_REGISTRY_CLASS_ORDER_INVALID", "runtime_allowed": False}
    model_path = Path(str(data.get("model_path") or ""))
    if not data.get("runtime_allowed") or not model_path.exists():
        return {"status": "MODEL_REGISTRY_MODEL_NOT_READY", "runtime_allowed": False, **data}
    return {"status": "MODEL_REGISTRY_READY", "runtime_allowed": True, **data}
