"""YOLOv8 single-class pohon_sono adapter for Plan C snapshots."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

from .paths import PROJECT_ROOT

RUNTIME_MODE = "PLAN_C_SINGLE_CLASS_POHON_SONO"
MODEL_POLICY = "single_class_pohon_sono"
ACTIVE_CLASS_NAME = "pohon_sono"
DETECTOR_NAME = "YOLOv8"
READY_STATUS = "YOLOV8_SINGLE_CLASS_POHON_SONO_READY"
REVIEW_STATUS = "YOLOV8_MODEL_READY_CLASS_MAPPING_REVIEW_REQUIRED"
MODEL_NOT_READY_STATUS = "YOLO_MODEL_NOT_READY"

MODEL_CANDIDATES = [
    PROJECT_ROOT / "models" / "plan_c_ai_detector" / "best.pt",
    PROJECT_ROOT / "models" / "plan_c_ai_detector" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt",
    PROJECT_ROOT / "weights" / "best.pt",
]

MULTICLASS_FALLBACK_CANDIDATES = [
    PROJECT_ROOT / "runs" / "detect" / "field_multiclass_v1" / "weights" / "best.pt",
]

PLAN_C_AI_REGISTRY = PROJECT_ROOT / "models" / "plan_c_ai_detector" / "registry.json"


def resolve_plan_c_yolo_model() -> dict[str, Any]:
    """Resolve the current Plan C YOLOv8 model without enabling multi-class runtime."""

    registry = _read_registry()
    checked = [str(path) for path in [*MODEL_CANDIDATES, *MULTICLASS_FALLBACK_CANDIDATES]]
    candidates = _candidate_paths_from_registry(registry) + MODEL_CANDIDATES
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if path.exists():
            names = _registry_class_names(registry)
            warnings: list[str] = []
            status = READY_STATUS
            if names and ACTIVE_CLASS_NAME not in {_normalize_name(value) for value in names.values()}:
                status = REVIEW_STATUS
                warnings.append("MODEL_CLASS_MAPPING_REVIEW_REQUIRED_FOR_POHON_SONO_ONLY_RUNTIME")
            if len(names) > 1:
                warnings.append("MODEL_REGISTRY_HAS_MULTIPLE_CLASSES_FILTERED_TO_POHON_SONO_RUNTIME")
            return _model_status_payload(
                status=status,
                model_path=path,
                checked_paths=checked,
                model_source="plan_c_registered_or_single_class_candidate",
                registry=registry,
                warnings=warnings,
            )

    for path in MULTICLASS_FALLBACK_CANDIDATES:
        if path.exists():
            return _model_status_payload(
                status=REVIEW_STATUS,
                model_path=path,
                checked_paths=checked,
                model_source="legacy_multiclass_fallback",
                registry=registry,
                warnings=["MULTICLASS_MODEL_FALLBACK_NOT_RECOMMENDED_FOR_CURRENT_SINGLE_CLASS_RUNTIME"],
            )

    return _base_policy_payload(
        {
            "status": MODEL_NOT_READY_STATUS,
            "model_path": "",
            "checked_paths": checked,
            "manual_review_required": True,
            "detections": [],
            "detection_count": 0,
            "warnings": ["YOLOv8 model file for pohon_sono runtime was not found."],
            "registry_status": _single_class_registry_status(registry.get("status") if registry else "REGISTRY_NOT_FOUND"),
            "not_accuracy_claim": True,
        }
    )


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
    if model_info["status"] == MODEL_NOT_READY_STATUS:
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
        _copy_with_label(original_path, annotated_path, "YOLOV8_RUNTIME_UNAVAILABLE - manual review required")
        return {
            **model_info,
            "status": "YOLOV8_RUNTIME_UNAVAILABLE",
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
        detections = _parse_pohon_sono_detections(result, status=str(model_info.get("status") or ""))
        _save_single_class_annotation(original_path, annotated_path, detections)
        return {
            **model_info,
            "runtime_status": "YOLOV8_PREDICT_COMPLETED",
            "runtime": {"conf": conf, "iou": iou, "imgsz": imgsz, "max_det": max_det},
            "detections": detections,
            "detection_count": len(detections),
            "annotated_path": str(annotated_path),
            "manual_review_required": len(detections) == 0 or model_info["status"] == REVIEW_STATUS,
            "not_accuracy_claim": True,
        }
    except Exception as exc:
        _copy_with_label(original_path, annotated_path, "YOLOV8_INFERENCE_FAILED - manual review required")
        return {
            **model_info,
            "status": "YOLOV8_INFERENCE_FAILED",
            "runtime_status": "YOLOV8_PREDICT_FAILED",
            "runtime_error": f"{type(exc).__name__}: {exc}",
            "detections": [],
            "detection_count": 0,
            "annotated_path": str(annotated_path),
            "manual_review_required": True,
            "risk_status": "DATA_TIDAK_CUKUP",
        }


def _parse_pohon_sono_detections(result: Any, *, status: str) -> list[dict[str, Any]]:
    if result is None or getattr(result, "boxes", None) is None:
        return []
    names = getattr(result, "names", {}) or {}
    pohon_ids = _pohon_sono_model_class_ids(names)
    detections: list[dict[str, Any]] = []
    for index, box in enumerate(result.boxes):
        model_cls_id = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else -1
        if model_cls_id not in pohon_ids and not _accept_unclear_single_class(model_cls_id, names, status):
            continue
        confidence = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else None
        xyxy = box.xyxy[0].tolist() if getattr(box, "xyxy", None) is not None else []
        xywhn = box.xywhn[0].tolist() if getattr(box, "xywhn", None) is not None else []
        label_conf = f"{float(confidence):.2f}" if confidence is not None else "review"
        detections.append(
            {
                "id": index,
                "class_id": 0,
                "model_class_id": model_cls_id,
                "class_name": ACTIVE_CLASS_NAME,
                "operator_label": ACTIVE_CLASS_NAME,
                "confidence": round(confidence, 4) if confidence is not None else None,
                "bbox_format": "xyxy",
                "bbox_xyxy": [round(float(value), 2) for value in xyxy],
                "bbox_xywhn": [round(float(value), 6) for value in xywhn],
                "source": "yolo_v8_single_class",
                "label": f"YOLOv8 pohon_sono {label_conf}",
                "review_status": "REVIEW",
                "reason": "Runtime Plan C hanya memakai target pohon_sono.",
            }
        )
    return detections


def _pohon_sono_model_class_ids(names: Any) -> set[int]:
    if not isinstance(names, dict):
        return {0}
    ids = {int(key) for key, value in names.items() if _normalize_name(value) == ACTIVE_CLASS_NAME}
    if len(names) == 1 and _normalize_name(next(iter(names.values()), "")) in {ACTIVE_CLASS_NAME, "tree"}:
        ids.add(0)
    return ids


def _accept_unclear_single_class(model_cls_id: int, names: Any, status: str) -> bool:
    return model_cls_id == 0 and status == REVIEW_STATUS and (not isinstance(names, dict) or not names)


def _save_single_class_annotation(original_path: Path, annotated_path: Path, detections: list[dict[str, Any]]) -> None:
    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore

        image = Image.open(original_path).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
        font = ImageFont.load_default()
        if detections:
            for detection in detections:
                _draw_pohon_box(draw, detection, font)
            _draw_badge(draw, image.size, f"YOLOv8 pohon_sono: {len(detections)}", font, fill=(18, 102, 48, 220))
        else:
            _draw_badge(
                draw,
                image.size,
                "YOLOV8_POHON_SONO_NOT_DETECTED - manual review required",
                font,
                fill=(31, 41, 55, 225),
            )
        image.save(annotated_path, quality=92)
    except Exception:
        shutil.copy2(original_path, annotated_path)


def _draw_pohon_box(draw: Any, detection: dict[str, Any], font: Any) -> None:
    bbox = detection.get("bbox_xyxy") or []
    if not isinstance(bbox, list) or len(bbox) != 4:
        return
    x1, y1, x2, y2 = [float(value) for value in bbox]
    color = (22, 163, 74, 255)
    for offset in range(3):
        draw.rectangle([x1 - offset, y1 - offset, x2 + offset, y2 + offset], outline=color)
    confidence = detection.get("confidence")
    label_conf = f"{float(confidence):.2f}" if isinstance(confidence, (int, float)) else "review"
    label = f"YOLOv8 pohon_sono {label_conf}"
    text_box = draw.textbbox((x1, y1), label, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    label_y = max(y1 - text_h - 8, 0)
    draw.rectangle([x1, label_y, x1 + text_w + 8, label_y + text_h + 6], fill=(22, 163, 74, 230))
    draw.text((x1 + 4, label_y + 3), label, fill=(255, 255, 255, 255), font=font)


def _draw_badge(draw: Any, size: tuple[int, int], text: str, font: Any, *, fill: tuple[int, int, int, int]) -> None:
    width, _height = size
    text_box = draw.textbbox((0, 0), text, font=font)
    text_w = min(text_box[2] - text_box[0], max(width - 32, 0))
    text_h = text_box[3] - text_box[1]
    draw.rectangle([10, 10, min(18 + text_w + 10, width - 10), 18 + text_h + 10], fill=fill)
    draw.text((18, 18), text[:96], fill=(255, 255, 255, 255), font=font)


def _copy_with_label(original_path: Path, annotated_path: Path, label: str) -> None:
    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore

        image = Image.open(original_path).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
        font = ImageFont.load_default()
        _draw_badge(draw, image.size, label, font, fill=(31, 41, 55, 225))
        image.save(annotated_path, quality=92)
    except Exception:
        shutil.copy2(original_path, annotated_path)


def _model_status_payload(
    *,
    status: str,
    model_path: Path,
    checked_paths: list[str],
    model_source: str,
    registry: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    return _base_policy_payload(
        {
            "status": status,
            "model_path": str(model_path),
            "checked_paths": checked_paths,
            "model_source": model_source,
            "registry_status": _single_class_registry_status(registry.get("status") if registry else "REGISTRY_NOT_FOUND"),
            "registry_path": str(PLAN_C_AI_REGISTRY),
            "manual_review_required": status != READY_STATUS,
            "warnings": warnings,
            "not_accuracy_claim": True,
        }
    )


def _base_policy_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        {
            "runtime_mode": RUNTIME_MODE,
            "detector": DETECTOR_NAME,
            "runtime_detector": DETECTOR_NAME,
            "model_policy": MODEL_POLICY,
            "active_class_names": [ACTIVE_CLASS_NAME],
            "active_detection_target": ACTIVE_CLASS_NAME,
            "yolo_mode": "single_class",
            "multi_class_runtime": False,
            "conductor_detection_enabled": False,
            "structure_detection_enabled": False,
            "conductor_required_for_detection": False,
        }
    )
    return payload


def _read_registry() -> dict[str, Any]:
    if not PLAN_C_AI_REGISTRY.exists():
        return {}
    try:
        return json.loads(PLAN_C_AI_REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "REGISTRY_READ_FAILED"}


def _candidate_paths_from_registry(registry: dict[str, Any]) -> list[Path]:
    candidates: list[Path] = []
    for key in ("best_pt", "model_path"):
        value = str(registry.get(key) or "").strip()
        if not value:
            continue
        path = Path(value)
        candidates.append(path if path.is_absolute() else PROJECT_ROOT / path)
    return candidates


def _registry_class_names(registry: dict[str, Any]) -> dict[int, str]:
    raw = registry.get("class_names") or registry.get("classes") or {}
    if not isinstance(raw, dict):
        return {}
    names: dict[int, str] = {}
    for key, value in raw.items():
        try:
            names[int(key)] = str(value)
        except (TypeError, ValueError):
            continue
    return names


def _normalize_name(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _single_class_registry_status(value: Any) -> str:
    text = str(value or "").strip()
    if text == "PLAN_C_AI_MODEL_READY":
        return "PLAN_C_REGISTERED_MODEL_READY_FOR_YOLOV8_SINGLE_CLASS_RUNTIME"
    if text == "PLAN_C_AI_MODEL_NOT_READY":
        return "PLAN_C_REGISTERED_MODEL_NOT_READY_FOR_YOLOV8_SINGLE_CLASS_RUNTIME"
    return text or "REGISTRY_STATUS_UNKNOWN"
