"""YOLO post-capture adapter for Plan C."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

from .paths import PROJECT_ROOT

MODEL_CANDIDATES = [
    PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "detect" / "field_multiclass_v1" / "weights" / "best.pt",
    PROJECT_ROOT / "weights" / "best.pt",
    PROJECT_ROOT / "models" / "best.pt",
]


def resolve_plan_c_yolo_model() -> dict[str, Any]:
    checked = [str(path) for path in MODEL_CANDIDATES]
    try:
        from .plan_c_system_c_runtime_selector import select_plan_c_runtime_model

        registry_model = select_plan_c_runtime_model()
        if registry_model.get("status") == "PLAN_C_RUNTIME_MODEL_FROM_SYSTEM_C_REGISTRY":
            return {
                "status": "YOLO_MODEL_READY",
                "model_path": str(registry_model.get("model_path") or ""),
                "checked_paths": ["System C model registry", *checked],
                "model_source": "system_c_registry",
                "registry_status": registry_model.get("registry_status"),
                "not_accuracy_claim": True,
            }
    except Exception as exc:
        registry_error = f"{type(exc).__name__}: {exc}"
    else:
        registry_error = ""
    for path in MODEL_CANDIDATES:
        if path.exists():
            return {
                "status": "YOLO_MODEL_READY",
                "model_path": str(path),
                "checked_paths": checked,
                "model_source": "legacy_candidate_path",
                "not_accuracy_claim": True,
            }
    return {
        "status": "YOLO_MODEL_NOT_READY",
        "model_path": "",
        "checked_paths": checked,
        "registry_error": registry_error,
        "manual_review_required": True,
        "not_accuracy_claim": True,
    }


def run_yolo_post_capture(
    original_path: Path,
    annotated_path: Path,
    *,
    conf: float = 0.25,
    iou: float = 0.5,
    imgsz: int = 640,
    max_det: int = 100,
) -> dict[str, Any]:
    model_info = resolve_plan_c_yolo_model()
    if model_info["status"] != "YOLO_MODEL_READY":
        _copy_with_label(original_path, annotated_path, "YOLO_MODEL_NOT_READY - manual review required")
        return {
            **model_info,
            "detections": [],
            "detection_count": 0,
            "annotated_path": str(annotated_path),
            "manual_review_required": True,
            "risk_status": "DATA_TIDAK_CUKUP",
        }

    try:
        from ultralytics import YOLO  # type: ignore
    except Exception as exc:
        _copy_with_label(original_path, annotated_path, "YOLO_RUNTIME_UNAVAILABLE - manual review required")
        return {
            **model_info,
            "status": "YOLO_RUNTIME_UNAVAILABLE",
            "runtime_status": "ULTRALYTICS_NOT_AVAILABLE",
            "runtime_error": f"{type(exc).__name__}: {exc}",
            "detections": [],
            "detection_count": 0,
            "annotated_path": str(annotated_path),
            "manual_review_required": True,
            "risk_status": "DATA_TIDAK_CUKUP",
        }

    try:
        model = YOLO(model_info["model_path"])
        results = model.predict(
            source=str(original_path),
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            max_det=max_det,
            save=False,
            verbose=False,
        )
        result = results[0] if results else None
        detections = _parse_detections(result)
        _save_result_plot(result, original_path, annotated_path)
        return {
            **model_info,
            "runtime_status": "YOLO_PREDICT_COMPLETED",
            "runtime": {"conf": conf, "iou": iou, "imgsz": imgsz, "max_det": max_det},
            "detections": detections,
            "detection_count": len(detections),
            "annotated_path": str(annotated_path),
            "manual_review_required": len(detections) == 0,
            "not_accuracy_claim": True,
        }
    except Exception as exc:
        _copy_with_label(original_path, annotated_path, "YOLO_INFERENCE_FAILED - manual review required")
        return {
            **model_info,
            "status": "YOLO_INFERENCE_FAILED",
            "runtime_status": "YOLO_PREDICT_FAILED",
            "runtime_error": f"{type(exc).__name__}: {exc}",
            "detections": [],
            "detection_count": 0,
            "annotated_path": str(annotated_path),
            "manual_review_required": True,
            "risk_status": "DATA_TIDAK_CUKUP",
        }


def _parse_detections(result: Any) -> list[dict[str, Any]]:
    if result is None or getattr(result, "boxes", None) is None:
        return []
    boxes = result.boxes
    names = getattr(result, "names", {}) or {}
    detections: list[dict[str, Any]] = []
    for index, box in enumerate(boxes):
        cls_id = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else -1
        confidence = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else None
        xyxy = box.xyxy[0].tolist() if getattr(box, "xyxy", None) is not None else []
        class_name = _safe_class_name(cls_id, names)
        detections.append(
            {
                "id": index,
                "class_id": cls_id,
                "class_name": class_name,
                "confidence": round(confidence, 4) if confidence is not None else None,
                "bbox_xyxy": [round(float(value), 2) for value in xyxy],
                "source": "yolo_post_capture",
            }
        )
    return detections


def _safe_class_name(cls_id: int, names: dict[Any, Any]) -> str:
    if len(names) == 1 and cls_id == 0:
        return "pohon_sono"
    raw_name = names.get(cls_id) if isinstance(names, dict) else None
    if raw_name:
        return str(raw_name)
    return f"unknown_class_{cls_id}"


def _save_result_plot(result: Any, original_path: Path, annotated_path: Path) -> None:
    try:
        plotted = result.plot()
        from PIL import Image  # type: ignore

        Image.fromarray(plotted).save(annotated_path)
    except Exception:
        shutil.copy2(original_path, annotated_path)


def _copy_with_label(original_path: Path, annotated_path: Path, label: str) -> None:
    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw  # type: ignore

        image = Image.open(original_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        x1, y1, x2, y2 = 8, 8, min(image.width - 8, 430), 34
        draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255), outline=(30, 30, 30))
        draw.text((14, 14), label, fill=(30, 30, 30))
        image.save(annotated_path, quality=92)
    except Exception:
        shutil.copy2(original_path, annotated_path)
