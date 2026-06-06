"""Safe YOLO inference wrapper with explicit unstable-model statuses."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from .yolo_label_audit import IMAGE_EXTENSIONS


def normalize_model_names(names: Any) -> dict[int, str]:
    if names is None:
        return {}
    if isinstance(names, dict):
        return {int(key): str(value) for key, value in names.items()}
    if isinstance(names, list):
        return {index: str(value) for index, value in enumerate(names)}
    return {}


def validate_single_class_pohon_sono_names(names: Any) -> dict[str, Any]:
    normalized = normalize_model_names(names)
    if normalized == {0: "pohon_sono"}:
        return {"status": "V001_SINGLE_CLASS_MODEL_OK", "names": normalized, "class_count": 1, "rejection_reason": ""}
    if len(normalized) > 1:
        return {
            "status": "WRONG_MODEL_MULTICLASS_REJECTED",
            "names": normalized,
            "class_count": len(normalized),
            "rejection_reason": "V001 safe pipeline requires exactly one class: 0 pohon_sono.",
        }
    return {
        "status": "WRONG_MODEL_SINGLE_CLASS_NAME_REJECTED",
        "names": normalized,
        "class_count": len(normalized),
        "rejection_reason": "Model class names must be exactly {0: 'pohon_sono'}.",
    }


def load_model(model_path: str | Path) -> dict[str, Any]:
    path = Path(model_path)
    if not path.exists():
        return {"status": "MODEL_NOT_READY", "model_path": str(path), "model": None, "error": "MODEL_FILE_NOT_FOUND"}
    try:
        from ultralytics import YOLO  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local env
        return {"status": "MODEL_NOT_READY", "model_path": str(path), "model": None, "error": f"ULTRALYTICS_IMPORT_FAILED: {exc}"}
    try:
        return {"status": "MODEL_LOADED", "model_path": str(path), "model": YOLO(str(path)), "error": None}
    except Exception as exc:  # pragma: no cover - depends on model artifact
        return {"status": "MODEL_NOT_READY", "model_path": str(path), "model": None, "error": f"MODEL_LOAD_FAILED: {exc}"}


def run_safe_predict(
    model_path: str | Path,
    source: str | Path,
    conf: float = 0.25,
    iou: float = 0.5,
    imgsz: int = 640,
    max_det: int = 20,
    allowed_classes: list[int] | None = None,
) -> dict[str, Any]:
    source_path = Path(source)
    image_count = _count_images(source_path)
    base = _empty_summary(model_path, source, conf, iou, imgsz, max_det, image_count)
    if conf < 0.01:
        base["warnings"].append("DIAGNOSTIC_LOW_CONF_ONLY")
        base["visual_allowed"] = False

    loaded = load_model(model_path)
    if loaded["status"] != "MODEL_LOADED":
        base["status"] = "MODEL_NOT_READY"
        base["warnings"].append(loaded.get("error", "MODEL_NOT_READY"))
        base["next_required_action"] = "Train and validate a real best.pt before runtime prediction."
        return base

    try:
        predict_kwargs: dict[str, Any] = {
            "source": str(source_path),
            "conf": conf,
            "iou": iou,
            "imgsz": imgsz,
            "max_det": max_det,
            "save": False,
            "save_txt": False,
            "verbose": False,
        }
        if allowed_classes is not None:
            predict_kwargs["classes"] = allowed_classes
        results = loaded["model"].predict(**predict_kwargs)
    except Exception as exc:  # pragma: no cover - depends on local YOLO runtime
        base["status"] = "MODEL_NOT_READY"
        base["warnings"].append(f"PREDICT_FAILED: {exc}")
        base["next_required_action"] = "Fix model/runtime loading error before operator prediction."
        return base

    summary = summarize_predictions(results)
    summary.update(
        {
            "model_path": str(model_path),
            "source": str(source),
            "conf": conf,
            "iou": iou,
            "imgsz": imgsz,
            "max_det": max_det,
            "image_count": max(image_count, summary.get("image_count", 0)),
            "visual_allowed": conf >= 0.01,
        }
    )
    if conf < 0.01:
        summary.setdefault("warnings", []).append("DIAGNOSTIC_LOW_CONF_ONLY")
    status = classify_model_runtime_status(summary)
    summary["status"] = status
    summary["next_required_action"] = _next_required_action(status)
    return summary


def summarize_predictions(results: Any) -> dict[str, Any]:
    detections = []
    detections_per_image: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    confidences: list[float] = []
    result_list = list(results) if results is not None else []
    for index, result in enumerate(result_list):
        image_path = str(getattr(result, "path", f"image_{index}"))
        names = getattr(result, "names", {}) or {}
        boxes = getattr(result, "boxes", None)
        cls_values = _to_list(getattr(boxes, "cls", [])) if boxes is not None else []
        conf_values = _to_list(getattr(boxes, "conf", [])) if boxes is not None else []
        image_count = min(len(cls_values), len(conf_values))
        detections_per_image[image_path] = image_count
        for det_index in range(image_count):
            class_id = int(float(cls_values[det_index]))
            confidence = float(conf_values[det_index])
            class_name = names.get(class_id, str(class_id)) if isinstance(names, dict) else str(class_id)
            detection = {
                "image": image_path,
                "class_id": class_id,
                "class_name": class_name,
                "confidence": confidence,
            }
            detections.append(detection)
            confidences.append(confidence)
            key = str(class_name)
            class_counts[key] = class_counts.get(key, 0) + 1

    confidence_stats = _confidence_stats(confidences)
    return {
        "status": "UNCLASSIFIED",
        "image_count": len(result_list),
        "total_detections": len(detections),
        "detections": detections,
        "detections_per_image": detections_per_image,
        "class_counts": class_counts,
        "confidence_stats": confidence_stats,
        "warnings": [],
        "next_required_action": "",
    }


def classify_model_runtime_status(summary: dict[str, Any]) -> str:
    if summary.get("status") == "MODEL_NOT_READY":
        return "MODEL_NOT_READY"
    total = int(summary.get("total_detections", 0))
    conf = float(summary.get("conf", 0.25))
    max_det = int(summary.get("max_det", 20))
    image_count = max(int(summary.get("image_count", 0)), 1)
    detections_per_image = summary.get("detections_per_image", {}) or {}
    per_image_counts = [int(value) for value in detections_per_image.values()] or [0]
    max_per_image = max(per_image_counts)
    avg_per_image = total / image_count
    confidence_stats = summary.get("confidence_stats", {}) or {}
    median_conf = confidence_stats.get("median")
    low_conf_share = float(confidence_stats.get("below_0_01_share", 0.0) or 0.0)

    if total == 0:
        return "MODEL_WEAK_NO_DETECTION"
    if max_per_image >= 100 or avg_per_image >= 100 or (conf <= 0.01 and max_per_image >= max_det):
        return "MODEL_UNSTABLE_TOO_MANY_BOXES"
    if conf < 0.01:
        return "MODEL_UNSTABLE_LOW_CONF"
    if median_conf is not None and float(median_conf) < 0.01 and low_conf_share >= 0.8:
        return "MODEL_UNSTABLE_TOO_MANY_BOXES"
    return "V001_SMOKE_MODEL_CANDIDATE"


def save_prediction_summary_json(summary: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(summary), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _empty_summary(
    model_path: str | Path,
    source: str | Path,
    conf: float,
    iou: float,
    imgsz: int,
    max_det: int,
    image_count: int,
) -> dict[str, Any]:
    return {
        "status": "MODEL_NOT_READY",
        "model_path": str(model_path),
        "source": str(source),
        "conf": conf,
        "iou": iou,
        "imgsz": imgsz,
        "max_det": max_det,
        "image_count": image_count,
        "total_detections": 0,
        "detections": [],
        "detections_per_image": {},
        "class_counts": {},
        "confidence_stats": _confidence_stats([]),
        "warnings": [],
        "visual_allowed": conf >= 0.01,
        "next_required_action": "",
    }


def _confidence_stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"min": None, "median": None, "max": None, "mean": None, "below_0_01_share": 0.0}
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "below_0_01_share": sum(1 for value in values if value < 0.01) / len(values),
    }


def _to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


def _count_images(source: Path) -> int:
    if source.is_file():
        return 1 if source.suffix.lower() in IMAGE_EXTENSIONS else 0
    if source.is_dir():
        return len([path for path in source.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS])
    return 0


def _next_required_action(status: str) -> str:
    actions = {
        "MODEL_NOT_READY": "Build/train a real V001 model first; keep runtime in MODEL_NOT_READY safe mode.",
        "MODEL_WEAK_NO_DETECTION": "Collect more labels or retrain; do not use this model for operator detection.",
        "MODEL_UNSTABLE_LOW_CONF": "Reject ultra-low-confidence output; train a stronger model before visualization.",
        "MODEL_UNSTABLE_TOO_MANY_BOXES": "Reject visualization and keep max_det/conf guards enabled.",
        "V001_SMOKE_MODEL_CANDIDATE": "Use only for limited smoke review, not final runtime readiness.",
    }
    return actions.get(status, "Review model status before runtime use.")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items() if key != "model"}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
