"""YOLOv8 adapter for Plan C System C snapshots."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

from .paths import PROJECT_ROOT
from .plan_c_inference_optimizer import run_optimized_yolo_inference, summarize_detection_quality

RUNTIME_MODE = "PLAN_C_SYSTEM_C"
SYSTEM_C_MODEL_POLICY = "system_c_detector"
SINGLE_CLASS_MODEL_POLICY = "single_class_pohon_sono"
ACTIVE_CLASS_NAME = "pohon_sono"
DETECTOR_NAME = "YOLOv8"
SYSTEM_C_READY_STATUS = "PLAN_C_SYSTEM_C_DETECTOR_READY"
READY_STATUS = "YOLOV8_SINGLE_CLASS_POHON_SONO_READY"
REVIEW_STATUS = "YOLOV8_MODEL_READY_CLASS_MAPPING_REVIEW_REQUIRED"
MODEL_NOT_READY_STATUS = "YOLO_MODEL_NOT_READY"
TARGET_CLASS_NAMES = {
    0: "struktur_penyangga",
    1: "konduktor",
    2: "pohon_sono",
    3: "pohon_non_sono",
}

MODEL_CANDIDATES = [
    PROJECT_ROOT / "models" / "plan_c_system_c_detector" / "best.pt",
    PROJECT_ROOT / "models" / "plan_c_ai_detector" / "best.pt",
    PROJECT_ROOT / "models" / "plan_c_ai_detector" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "detect" / "plan_c_system_c_detector_v2" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt",
    PROJECT_ROOT / "weights" / "best.pt",
]

MULTICLASS_FALLBACK_CANDIDATES = [
    PROJECT_ROOT / "runs" / "detect" / "field_multiclass_v1" / "weights" / "best.pt",
]

PLAN_C_AI_REGISTRY = PROJECT_ROOT / "models" / "plan_c_ai_detector" / "registry.json"
PLAN_C_SYSTEM_C_REGISTRY = PROJECT_ROOT / "models" / "plan_c_system_c_detector" / "registry.json"


def resolve_plan_c_yolo_model() -> dict[str, Any]:
    """Resolve the current Plan C YOLOv8 model with System C priority and safe fallback."""

    registry = _read_registry()
    system_run_candidates = _system_c_run_candidates()
    checked = [str(path) for path in [*MODEL_CANDIDATES, *system_run_candidates, *MULTICLASS_FALLBACK_CANDIDATES]]
    candidates = _candidate_paths_from_registry(registry) + MODEL_CANDIDATES + system_run_candidates
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if path.exists():
            names = _registry_class_names(registry)
            warnings: list[str] = []
            model_policy = _model_policy_for_path(path, registry)
            status = SYSTEM_C_READY_STATUS if model_policy == SYSTEM_C_MODEL_POLICY else READY_STATUS
            normalized_names = {_normalize_name(value) for value in names.values()}
            if model_policy == SINGLE_CLASS_MODEL_POLICY and names and ACTIVE_CLASS_NAME not in normalized_names:
                status = REVIEW_STATUS
                warnings.append("MODEL_CLASS_MAPPING_REVIEW_REQUIRED_FOR_POHON_SONO_ONLY_RUNTIME")
            if model_policy == SINGLE_CLASS_MODEL_POLICY and len(names) > 1:
                warnings.append("MODEL_REGISTRY_HAS_MULTIPLE_CLASSES_FILTERED_TO_POHON_SONO_RUNTIME")
            return _model_status_payload(
                status=status,
                model_path=path,
                checked_paths=checked,
                model_source="plan_c_system_c_or_single_class_candidate",
                registry=registry,
                warnings=warnings,
                model_policy=model_policy,
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
                model_policy=SINGLE_CLASS_MODEL_POLICY,
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
        def _predict_variant(path: Path, variant_conf: float, variant_iou: float, variant_imgsz: int, variant_max_det: int) -> list[dict[str, Any]]:
            results = model.predict(
                source=str(path),
                conf=variant_conf,
                iou=variant_iou,
                imgsz=variant_imgsz,
                max_det=variant_max_det,
                save=False,
                verbose=False,
            )
            result = results[0] if results else None
            return _parse_plan_c_detections(result, model_info=model_info)

        optimized = run_optimized_yolo_inference(
            original_path,
            predict_callback=_predict_variant,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            max_det=max_det,
            model_policy=str(model_info.get("model_policy") or SINGLE_CLASS_MODEL_POLICY),
        )
        detections = optimized["detections"]
        _save_single_class_annotation(original_path, annotated_path, detections)
        return {
            **model_info,
            "runtime_status": "YOLOV8_PREDICT_COMPLETED",
            "runtime": {"conf": conf, "iou": iou, "imgsz": imgsz, "max_det": max_det},
            "detections": detections,
            "detection_count": len(detections),
            "class_counts": _class_counts(detections),
            "annotated_path": str(annotated_path),
            "manual_review_required": len(detections) == 0 or model_info["status"] == REVIEW_STATUS,
            "not_accuracy_claim": True,
            "image_quality": optimized.get("image_quality", {}),
            "image_quality_status": optimized.get("image_quality", {}).get("status"),
            "image_quality_reasons": optimized.get("image_quality", {}).get("reasons", []),
            "inference_optimization": optimized.get("inference_optimization", {}),
            "raw_detection_count": optimized.get("raw_detection_count", 0),
            "merged_detection_count": optimized.get("merged_detection_count", 0),
            "rejected_detections_redacted": optimized.get("rejected_detections_redacted", []),
            "detection_quality_summary": summarize_detection_quality(detections, optimized.get("image_quality", {})),
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


def _parse_plan_c_detections(result: Any, *, model_info: dict[str, Any]) -> list[dict[str, Any]]:
    if result is None or getattr(result, "boxes", None) is None:
        return []
    names = getattr(result, "names", {}) or {}
    model_policy = str(model_info.get("model_policy") or SINGLE_CLASS_MODEL_POLICY)
    class_map = _runtime_class_map(names, model_policy=model_policy, status=str(model_info.get("status") or ""))
    detections: list[dict[str, Any]] = []
    for index, box in enumerate(result.boxes):
        model_cls_id = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else -1
        target_name = class_map.get(model_cls_id)
        if not target_name:
            continue
        confidence = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else None
        xyxy = box.xyxy[0].tolist() if getattr(box, "xyxy", None) is not None else []
        xywhn = box.xywhn[0].tolist() if getattr(box, "xywhn", None) is not None else []
        label_conf = f"{float(confidence):.2f}" if confidence is not None else "review"
        output_class_id = _target_class_id(target_name)
        detections.append(
            {
                "id": index,
                "class_id": output_class_id,
                "model_class_id": model_cls_id,
                "class_name": target_name,
                "operator_label": target_name,
                "confidence": round(confidence, 4) if confidence is not None else None,
                "bbox_format": "xyxy",
                "bbox_xyxy": [round(float(value), 2) for value in xyxy],
                "bbox_xywhn": [round(float(value), 6) for value in xywhn],
                "source": "yolo_v8_system_c_detector" if model_policy == SYSTEM_C_MODEL_POLICY else "yolo_v8_single_class",
                "label": f"YOLOv8 {target_name} {label_conf}",
                "review_status": "REVIEW",
                "reason": "Runtime Plan C memakai target System C yang tersedia pada model lokal.",
            }
        )
    return detections


def _runtime_class_map(names: Any, *, model_policy: str, status: str) -> dict[int, str]:
    if model_policy == SYSTEM_C_MODEL_POLICY:
        if not isinstance(names, dict) or not names:
            return {0: "struktur_penyangga", 1: "konduktor", 2: "pohon_sono"}
        mapped: dict[int, str] = {}
        for key, value in names.items():
            try:
                class_id = int(key)
            except (TypeError, ValueError):
                continue
            normalized = _normalize_name(value)
            if normalized in {"struktur_penyangga", "konduktor", "pohon_sono", "pohon_non_sono"}:
                mapped[class_id] = normalized
        return mapped
    if not isinstance(names, dict):
        return {0: ACTIVE_CLASS_NAME}
    mapped = {int(key): ACTIVE_CLASS_NAME for key, value in names.items() if _normalize_name(value) == ACTIVE_CLASS_NAME}
    if len(names) == 1 and _normalize_name(next(iter(names.values()), "")) in {ACTIVE_CLASS_NAME, "tree"}:
        mapped[0] = ACTIVE_CLASS_NAME
    if not mapped and _accept_unclear_single_class(0, names, status):
        mapped[0] = ACTIVE_CLASS_NAME
    return mapped


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
            _draw_badge(draw, image.size, f"YOLOv8 detections: {len(detections)}", font, fill=(18, 102, 48, 220))
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
    color = _class_color(str(detection.get("class_name") or "pohon_sono"))
    for offset in range(3):
        draw.rectangle([x1 - offset, y1 - offset, x2 + offset, y2 + offset], outline=color)
    confidence = detection.get("confidence")
    label_conf = f"{float(confidence):.2f}" if isinstance(confidence, (int, float)) else "review"
    label = f"YOLOv8 {detection.get('class_name') or 'pohon_sono'} {label_conf}"
    text_box = draw.textbbox((x1, y1), label, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    label_y = max(y1 - text_h - 8, 0)
    draw.rectangle([x1, label_y, x1 + text_w + 8, label_y + text_h + 6], fill=(*color[:3], 230))
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
    model_policy: str,
) -> dict[str, Any]:
    return _base_policy_payload(
        {
            "status": status,
            "model_path": str(model_path),
            "checked_paths": checked_paths,
            "model_source": model_source,
            "registry_status": _single_class_registry_status(registry.get("status") if registry else "REGISTRY_NOT_FOUND"),
            "registry_path": str(PLAN_C_AI_REGISTRY),
            "system_c_registry_path": str(PLAN_C_SYSTEM_C_REGISTRY),
            "model_policy": model_policy,
            "active_model_path": str(model_path),
            "manual_review_required": status not in {READY_STATUS, SYSTEM_C_READY_STATUS},
            "warnings": warnings,
            "not_accuracy_claim": True,
        }
    )


def _base_policy_payload(payload: dict[str, Any]) -> dict[str, Any]:
    model_policy = str(payload.get("model_policy") or SINGLE_CLASS_MODEL_POLICY)
    active_names = _active_class_names_for_policy(model_policy)
    payload.update(
        {
            "runtime_mode": RUNTIME_MODE,
            "detector": DETECTOR_NAME,
            "runtime_detector": DETECTOR_NAME,
            "model_policy": model_policy,
            "active_class_names": active_names,
            "active_detection_target": ACTIVE_CLASS_NAME,
            "yolo_mode": "object_detection",
            "multi_class_runtime": False,
            "conductor_detection_enabled": model_policy == SYSTEM_C_MODEL_POLICY,
            "structure_detection_enabled": model_policy == SYSTEM_C_MODEL_POLICY,
            "conductor_required_for_detection": False,
        }
    )
    return payload


def _read_registry() -> dict[str, Any]:
    system_registry = _read_registry_file(PLAN_C_SYSTEM_C_REGISTRY)
    if system_registry:
        system_registry["_registry_path"] = str(PLAN_C_SYSTEM_C_REGISTRY)
        return system_registry
    return _read_registry_file(PLAN_C_AI_REGISTRY)


def _read_registry_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
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


def _system_c_run_candidates() -> list[Path]:
    runs_dir = PROJECT_ROOT / "runs" / "detect"
    if not runs_dir.exists():
        return []
    candidates = [
        path / "weights" / "best.pt"
        for path in runs_dir.glob("plan_c_system_c_detector_v2*")
        if path.is_dir() and (path / "weights" / "best.pt").exists()
    ]
    return sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)


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


def _model_policy_for_path(path: Path, registry: dict[str, Any]) -> str:
    normalized = str(path).replace("\\", "/").lower()
    registry_status = str(registry.get("status") or "")
    class_policy = str(registry.get("class_policy") or "")
    if "plan_c_system_c_detector" in normalized or registry_status == SYSTEM_C_READY_STATUS or class_policy == "system_c_tree_conductor_structure":
        return SYSTEM_C_MODEL_POLICY
    return SINGLE_CLASS_MODEL_POLICY


def _active_class_names_for_policy(model_policy: str) -> list[str]:
    if model_policy == SYSTEM_C_MODEL_POLICY:
        return ["struktur_penyangga", "konduktor", "pohon_sono"]
    return [ACTIVE_CLASS_NAME]


def _target_class_id(class_name: str) -> int:
    for class_id, name in TARGET_CLASS_NAMES.items():
        if name == class_name:
            return class_id
    return 2


def _class_counts(detections: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for detection in detections:
        name = str(detection.get("class_name") or "unknown")
        counts[name] = counts.get(name, 0) + 1
    return counts


def _class_color(class_name: str) -> tuple[int, int, int, int]:
    if class_name == "konduktor":
        return (245, 158, 11, 255)
    if class_name == "struktur_penyangga":
        return (37, 99, 235, 255)
    if class_name == "pohon_non_sono":
        return (132, 204, 22, 255)
    return (22, 163, 74, 255)
