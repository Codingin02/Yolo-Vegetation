"""Centralized YOLO model status resolver for consistent runtime status across all endpoints.

This module ensures that model status is never UNKNOWN and is resolved consistently
across all APIs and runtime functions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

# Model path candidates
TREE_MODEL_PATH_V2 = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt"
TREE_MODEL_PATH_V1 = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt"
TREE_MODEL_CANDIDATES = [TREE_MODEL_PATH_V2, TREE_MODEL_PATH_V1]

MULTICLASS_MODEL_CANDIDATES = [
    PROJECT_ROOT / "models" / "field" / "field_multiclass_best.pt",
    PROJECT_ROOT / "runs" / "detect" / "field_multiclass_v1" / "weights" / "best.pt",
]

# Class definitions
PROJECT_CLASS_NAMES = {"pohon_sono", "konduktor", "struktur_penyangga"}
MULTICLASS_ALLOWED = {
    0: "struktur_penyangga",
    1: "konduktor",
    2: "pohon_sono",
}


def _find_tree_model_path() -> Path | None:
    """Find first available tree model from candidates."""
    for path in TREE_MODEL_CANDIDATES:
        if path.exists() and path.is_file():
            return path
    return None


def _find_multiclass_model_path() -> Path | None:
    """Find first available multiclass model from candidates."""
    for path in MULTICLASS_MODEL_CANDIDATES:
        if path.exists() and path.is_file():
            return path
    return None


def resolve_vision_runtime_status() -> dict[str, Any]:
    """
    Centralized resolver for vision runtime model status.

    This function NEVER returns MODEL_STATUS_UNKNOWN. It always returns
    a concrete status that can be used by all endpoints safely.

    Returns:
        dict with guaranteed fields:
        - tree_model_status: TREE_MODEL_READY_CANDIDATE or MODEL_NOT_READY
        - pole_model_status: POLE_MODEL_NOT_READY (not implemented)
        - conductor_model_status: CONDUCTOR_MODEL_NOT_READY (not implemented)
        - multiclass_model_status: MULTICLASS_MODEL_READY_CANDIDATE or MODEL_NOT_READY
        - runtime_model_status: YOLO_LOCAL_READY or MODEL_NOT_READY
        - allowed_classes: list of class names that can be detected
        - no_fake_detection: always True
        - model_exists: boolean
        - model_loadable: boolean (best effort check)
        - reason_codes: list of reason codes explaining status
    """
    tree_path = _find_tree_model_path()
    multiclass_path = _find_multiclass_model_path()

    # Determine tree model status
    if tree_path and tree_path.exists():
        tree_status = "TREE_MODEL_READY_CANDIDATE"
        model_exists = True
        reason_codes = ["TREE_MODEL_FOUND"]
    else:
        tree_status = "MODEL_NOT_READY"
        model_exists = False
        reason_codes = ["TREE_MODEL_NOT_FOUND"]

    # Determine multiclass status
    if multiclass_path and multiclass_path.exists():
        multiclass_status = "MULTICLASS_MODEL_READY_CANDIDATE"
        reason_codes.append("MULTICLASS_MODEL_FOUND")
    else:
        multiclass_status = "MODEL_NOT_READY"
        if not model_exists:
            reason_codes.append("MULTICLASS_MODEL_NOT_FOUND")

    # Determine runtime status (primary decision)
    # Prefer tree model if available, otherwise multiclass
    if tree_path and tree_path.exists():
        runtime_status = "YOLO_LOCAL_READY"
        allowed_classes = ["pohon_sono"]
        model_path = str(tree_path)
    elif multiclass_path and multiclass_path.exists():
        runtime_status = "YOLO_LOCAL_READY"
        allowed_classes = sorted(PROJECT_CLASS_NAMES)
        model_path = str(multiclass_path)
    else:
        runtime_status = "MODEL_NOT_READY"
        allowed_classes = []
        model_path = None

    return {
        "tree_model_status": tree_status,
        "pole_model_status": "POLE_MODEL_NOT_READY",
        "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
        "multiclass_model_status": multiclass_status,
        "runtime_model_status": runtime_status,
        "allowed_classes": allowed_classes,
        "no_fake_detection": True,
        "model_exists": model_exists,
        "model_loadable": model_exists,  # Basic check: file exists = loadable
        "model_path": model_path,
        "reason_codes": reason_codes,
        "clearance_status": "CLEARANCE_NOT_FINAL",
        "eta_status": "ETA_NOT_FINAL",
    }


def validate_model_loadable(model_path: str | None) -> dict[str, Any]:
    """
    Validate if a model file is loadable without actually loading it.

    Returns:
        dict with:
        - loadable: boolean
        - reason: reason code
        - error: error message if not loadable
    """
    if not model_path:
        return {"loadable": False, "reason": "NO_MODEL_PATH", "error": "Model path is None"}

    try:
        path = Path(model_path)
        if not path.exists():
            return {"loadable": False, "reason": "FILE_NOT_FOUND", "error": f"Path does not exist: {model_path}"}

        if not path.is_file():
            return {"loadable": False, "reason": "NOT_A_FILE", "error": f"Path is not a file: {model_path}"}

        # Check file size (models should be > 1MB)
        size_bytes = path.stat().st_size
        if size_bytes < 1_000_000:
            return {"loadable": False, "reason": "FILE_TOO_SMALL", "error": f"File size {size_bytes} bytes is suspiciously small"}

        return {"loadable": True, "reason": "FILE_EXISTS_AND_VALID_SIZE", "error": None}

    except Exception as exc:
        return {"loadable": False, "reason": "VALIDATION_ERROR", "error": str(exc)}


def get_yolo_readiness_response() -> dict[str, Any]:
    """
    Get the /api/runtime/yolo-readiness endpoint response.

    This is the API response that should be served at GET /api/runtime/yolo-readiness.

    Returns:
        API-ready response dict
    """
    status = resolve_vision_runtime_status()
    tree_path = _find_tree_model_path()

    return {
        "ok": True,
        "runtime_model_status": status["runtime_model_status"],
        "tree_model_status": status["tree_model_status"],
        "pole_model_status": status["pole_model_status"],
        "conductor_model_status": status["conductor_model_status"],
        "multiclass_model_status": status["multiclass_model_status"],
        "model_path": status["model_path"],
        "model_exists": status["model_exists"],
        "model_loadable": status["model_loadable"],
        "names": ["pohon_sono"] if status["runtime_model_status"] == "YOLO_LOCAL_READY" else [],
        "allowed_classes": status["allowed_classes"],
        "no_fake_detection": status["no_fake_detection"],
        "reason_codes": status["reason_codes"],
        "clearance_status": status["clearance_status"],
        "eta_status": status["eta_status"],
    }
