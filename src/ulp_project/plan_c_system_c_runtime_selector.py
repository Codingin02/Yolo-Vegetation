"""Runtime selector for Plan C System C final model registry."""

from __future__ import annotations

from typing import Any

from .plan_c_system_c_model_registry import load_model_registry


def select_plan_c_runtime_model() -> dict[str, Any]:
    registry = load_model_registry()
    if registry.get("status") == "MODEL_REGISTRY_READY" and registry.get("runtime_allowed"):
        return {
            "status": "PLAN_C_RUNTIME_MODEL_FROM_SYSTEM_C_REGISTRY",
            "model_path": registry.get("model_path", ""),
            "classes": registry.get("classes", []),
            "registry_status": registry.get("status"),
            "registry": registry,
        }
    return {
        "status": "PLAN_C_RUNTIME_MODEL_REGISTRY_NOT_READY",
        "model_path": "",
        "classes": [],
        "registry_status": registry.get("status"),
        "registry": registry,
    }
