"""Inference runtime scaffold with safe no-model behavior."""

from __future__ import annotations

from pathlib import Path

from .detection_result import DetectionRuntimeResult
from .paths import PROJECT_ROOT


MODEL_CANDIDATES = [
    PROJECT_ROOT / "weights" / "field_multiclass_v1.pt",
    PROJECT_ROOT / "runs" / "detect" / "field_multiclass_v1" / "weights" / "best.pt",
]


def resolve_model_path(model_path: str | Path | None = None) -> Path | None:
    if model_path:
        candidate = Path(model_path)
        return candidate if candidate.exists() else None
    for candidate in MODEL_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _no_model_result(input_path: str | Path, requested_model: str | Path | None = None) -> dict[str, object]:
    warnings = ["No trained YOLO field model is available."]
    if requested_model:
        warnings.append(f"Requested model not found: {requested_model}")
    return DetectionRuntimeResult(
        status="MODEL_NOT_READY",
        input_path=str(input_path),
        model_path=str(requested_model or ""),
        detections=[],
        warnings=warnings,
    ).to_dict()


def run_image_inference(input_path: str | Path, model_path: str | Path | None = None) -> dict[str, object]:
    model = resolve_model_path(model_path)
    if model is None:
        return _no_model_result(input_path, model_path)
    return DetectionRuntimeResult(
        status="MODEL_AVAILABLE_INFERENCE_NOT_IMPLEMENTED",
        input_path=str(input_path),
        model_path=str(model),
        detections=[],
        warnings=["Inference execution is intentionally scaffolded until final model validation."],
    ).to_dict()


def run_video_inference(input_path: str | Path, model_path: str | Path | None = None) -> dict[str, object]:
    model = resolve_model_path(model_path)
    if model is None:
        return _no_model_result(input_path, model_path)
    return DetectionRuntimeResult(
        status="MODEL_AVAILABLE_VIDEO_INFERENCE_NOT_IMPLEMENTED",
        input_path=str(input_path),
        model_path=str(model),
        detections=[],
        warnings=["Video inference is scaffolded and waits for final model validation."],
    ).to_dict()


def run_camera_inference(camera_index: int = 0, model_path: str | Path | None = None) -> dict[str, object]:
    model = resolve_model_path(model_path)
    if model is None:
        return _no_model_result(f"camera:{camera_index}", model_path)
    return DetectionRuntimeResult(
        status="MODEL_AVAILABLE_CAMERA_INFERENCE_NOT_IMPLEMENTED",
        input_path=f"camera:{camera_index}",
        model_path=str(model),
        detections=[],
        warnings=["Camera inference is scaffolded and waits for final model validation."],
    ).to_dict()
