"""Local AI Vision Detector runtime for Plan C upload mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

MODEL_USER_NAME = "AI Vision Detector"
INTERNAL_ENGINE = "Ultralytics YOLO object detection"
MODEL_PATH = PROJECT_ROOT / "models" / "plan_c_ai_detector" / "best.pt"
REGISTRY_PATH = PROJECT_ROOT / "models" / "plan_c_ai_detector" / "registry.json"
TRAINING_RESULTS_PATH = PROJECT_ROOT / "runs" / "detect" / "plan_c_ai_detector_v1" / "results.csv"

CLASS_NAMES = {
    0: "struktur_penyangga",
    1: "konduktor",
    2: "pohon_sono",
    3: "pohon_non_sono",
}

CLASS_COLORS = {
    "struktur_penyangga": (37, 99, 235),
    "konduktor": (245, 158, 11),
    "pohon_sono": (22, 163, 74),
    "pohon_non_sono": (132, 204, 22),
}

_MODEL_CACHE: Any | None = None


def load_plan_c_ai_model() -> dict[str, Any]:
    """Load the local detector when the model file is present."""

    global _MODEL_CACHE
    status = get_plan_c_ai_model_status()
    if status.get("status") != "PLAN_C_AI_MODEL_READY":
        return {**status, "model": None}
    if _MODEL_CACHE is not None:
        return {**status, "model": _MODEL_CACHE}
    try:
        from ultralytics import YOLO  # type: ignore

        _MODEL_CACHE = YOLO(str(MODEL_PATH))
        return {**status, "model": _MODEL_CACHE}
    except Exception as exc:
        return {
            **status,
            "status": "PLAN_C_AI_RUNTIME_UNAVAILABLE",
            "model": None,
            "runtime_error": f"{type(exc).__name__}: {exc}",
            "manual_review_required": True,
        }


def get_plan_c_ai_model_status() -> dict[str, Any]:
    registry = _read_registry()
    ready = MODEL_PATH.exists() and REGISTRY_PATH.exists()
    warnings: list[str] = [
        "CONDUCTOR_CLASS_WEAK_VALIDATION_SET_SMALL",
        "POHON_SONO_VALIDATION_SET_SMALL",
        "NOT_FINAL_PLN_ACCURACY_CLAIM",
    ]
    return {
        "status": "PLAN_C_AI_MODEL_READY" if ready else "PLAN_C_AI_MODEL_NOT_READY",
        "model_status": "PLAN_C_AI_MODEL_READY" if ready else "PLAN_C_AI_MODEL_NOT_READY",
        "model_user_name": MODEL_USER_NAME,
        "internal_engine": INTERNAL_ENGINE,
        "model_path": _relative(MODEL_PATH),
        "registry_path": _relative(REGISTRY_PATH),
        "training_results_path": _relative(TRAINING_RESULTS_PATH),
        "registry_exists": REGISTRY_PATH.exists(),
        "model_exists": MODEL_PATH.exists(),
        "training_results_exists": TRAINING_RESULTS_PATH.exists(),
        "registry": registry,
        "class_names": CLASS_NAMES,
        "warnings": warnings,
        "manual_review_required": not ready,
    }


def predict_plan_c_ai_objects(image_path: str | Path, conf: float = 0.25, imgsz: int = 640) -> dict[str, Any]:
    image_path = Path(image_path)
    status = get_plan_c_ai_model_status()
    if status.get("status") != "PLAN_C_AI_MODEL_READY":
        return {
            **status,
            "status": "PLAN_C_AI_MODEL_NOT_READY",
            "detections": [],
            "manual_review_required": True,
        }
    loaded = load_plan_c_ai_model()
    model = loaded.get("model")
    if model is None:
        return {
            **status,
            "status": loaded.get("status", "PLAN_C_AI_RUNTIME_UNAVAILABLE"),
            "detections": [],
            "manual_review_required": True,
            "warnings": [*status.get("warnings", []), loaded.get("runtime_error", "AI detector runtime unavailable")],
        }
    try:
        raw_results = model.predict(str(image_path), conf=conf, imgsz=imgsz, verbose=False, max_det=50)
        detections = normalize_detections(raw_results, image_path=image_path)
    except Exception as exc:
        return {
            **status,
            "status": "PLAN_C_AI_INFERENCE_FAILED",
            "detections": [],
            "manual_review_required": True,
            "warnings": [*status.get("warnings", []), f"{type(exc).__name__}: {exc}"],
        }
    warnings = list(status.get("warnings", []))
    if not any(item.get("class_name") == "konduktor" and float(item.get("confidence") or 0.0) >= 0.35 for item in detections):
        warnings.append("CONDUCTOR_CLASS_WEAK_OR_NOT_DETECTED")
    return {
        **status,
        "status": "PLAN_C_AI_DETECTION_READY",
        "detection_status": "PLAN_C_AI_DETECTION_READY",
        "detections": detections,
        "detection_count": len(detections),
        "manual_review_required": "CONDUCTOR_CLASS_WEAK_OR_NOT_DETECTED" in warnings or not detections,
        "warnings": warnings,
        "raw_summary": {
            "result_count": len(raw_results) if isinstance(raw_results, list) else 1,
            "conf": conf,
            "imgsz": imgsz,
        },
    }


def normalize_detections(raw_results: Any, *, image_path: Path | None = None) -> list[dict[str, Any]]:
    detections: list[dict[str, Any]] = []
    results = raw_results if isinstance(raw_results, list) else [raw_results]
    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        names = getattr(result, "names", {}) or {}
        for box in boxes:
            try:
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                xyxy = [float(value) for value in box.xyxy[0].tolist()]
                xywhn = [float(value) for value in box.xywhn[0].tolist()]
            except Exception:
                continue
            class_name = str(names.get(class_id) or CLASS_NAMES.get(class_id) or f"unknown_class_{class_id}")
            if class_id not in CLASS_NAMES:
                continue
            detections.append(
                {
                    "class_id": class_id,
                    "class_name": CLASS_NAMES[class_id] if class_name not in set(CLASS_NAMES.values()) else class_name,
                    "confidence": round(confidence, 4),
                    "bbox_xyxy": [round(value, 2) for value in xyxy],
                    "bbox_xywhn": [round(value, 6) for value in xywhn],
                    "source": MODEL_USER_NAME,
                }
            )
    return detections


def save_annotated_image(
    original_path: str | Path,
    annotated_path: str | Path,
    detections: list[dict[str, Any]],
    *,
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    original_path = Path(original_path)
    annotated_path = Path(annotated_path)
    summary = summary or {}
    try:
        from PIL import Image, ImageDraw, ImageFont

        image = Image.open(original_path).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
        font = ImageFont.load_default()
        _draw_detections(draw, detections, font=font)
        _draw_summary_badge(draw, image.size, summary, font=font)
        annotated_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(annotated_path, format="JPEG", quality=90)
        return {"status": "ANNOTATED_IMAGE_READY", "annotated_path": _relative(annotated_path)}
    except Exception as exc:
        try:
            annotated_path.write_bytes(original_path.read_bytes())
            return {
                "status": "ANNOTATED_IMAGE_FALLBACK_ORIGINAL_COPIED",
                "annotated_path": _relative(annotated_path),
                "warning": f"{type(exc).__name__}: {exc}",
            }
        except Exception as copy_exc:
            return {
                "status": "ANNOTATED_IMAGE_FAILED",
                "warning": f"{type(copy_exc).__name__}: {copy_exc}",
            }


def _draw_detections(draw: Any, detections: list[dict[str, Any]], *, font: Any) -> None:
    for detection in detections:
        box = detection.get("bbox_xyxy")
        if not isinstance(box, list) or len(box) != 4:
            continue
        class_name = str(detection.get("class_name") or "")
        color = CLASS_COLORS.get(class_name, (80, 80, 80))
        x1, y1, x2, y2 = [int(round(float(value))) for value in box]
        draw.rectangle([x1, y1, x2, y2], outline=(*color, 255), width=3)
        label = f"{class_name} {float(detection.get('confidence') or 0):.2f}"
        label_w = max(90, len(label) * 7)
        draw.rectangle([x1, max(0, y1 - 20), x1 + label_w, y1], fill=(*color, 220))
        draw.text((x1 + 4, max(0, y1 - 17)), label, fill=(255, 255, 255, 255), font=font)


def _draw_summary_badge(draw: Any, image_size: tuple[int, int], summary: dict[str, Any], *, font: Any) -> None:
    width, height = image_size
    risk_status = str(summary.get("risk_status") or "DATA_TIDAK_CUKUP")
    prediction = str(summary.get("prediction_window") or "data tidak cukup")
    review = str(summary.get("manual_review_required", True))
    warnings = summary.get("warnings") or []
    warning_text = ", ".join(str(item) for item in warnings[:2]) if isinstance(warnings, list) else str(warnings)
    lines = [
        f"Risk Zone: {risk_status}",
        f"Prediction Window: {prediction}",
        f"Manual Review Required: {review}",
    ]
    if warning_text:
        lines.append(f"Warnings: {warning_text}")
    badge_w = min(width - 16, max(330, max(len(line) for line in lines) * 7 + 18))
    badge_h = 18 * len(lines) + 12
    x1 = 8
    y1 = max(8, height - badge_h - 8)
    draw.rectangle([x1, y1, x1 + badge_w, y1 + badge_h], fill=(15, 23, 42, 210))
    for index, line in enumerate(lines):
        draw.text((x1 + 8, y1 + 7 + (index * 18)), line, fill=(255, 255, 255, 255), font=font)


def _read_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        return str(path).replace("\\", "/")
