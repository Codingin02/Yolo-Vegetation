"""Small facade around model handoff checks for scripts and gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .model_handoff import check_model_handoff, verify_model_class_order


def validate_model_runtime(model_path: str | Path | None = None, *, dry_load: bool = False, model_names: dict[int, str] | list[str] | None = None) -> dict[str, Any]:
    status = check_model_handoff(model_path, dry_load=dry_load)
    class_status = verify_model_class_order(model_names) if model_names is not None else {"status": status["class_order_status"]}
    if class_status["status"] == "MODEL_REJECTED_CLASS_ORDER_MISMATCH":
        status["model_status"] = "MODEL_REJECTED_CLASS_ORDER_MISMATCH"
        status["inference_status"] = "SKIPPED_CLASS_ORDER_MISMATCH"
    status["class_order_check"] = class_status
    return status
