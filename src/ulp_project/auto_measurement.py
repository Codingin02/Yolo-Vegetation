"""Auto YOLO measurement pipeline skeleton for vegetation clearance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .risk_action_policy import classify_eta_action
from .span_measurement import estimate_span_lowest_point, span_points_from_detections
from .temporal_stabilizer import TemporalStabilizer
from .vision_geometry import (
    bbox_bottom_y,
    bbox_center,
    bbox_height,
    bbox_top_y,
    height_above_reference_base,
    meter_per_pixel,
    object_height_from_bbox,
)
from .yolo_model_resolver import normalize_yolo_class_name, resolve_yolo_model

ASSET_PROFILE_PATH = PROJECT_ROOT / "configs" / "electrical_asset_profiles.yaml"
_STABILIZER = TemporalStabilizer(window_size=5, outlier_threshold_m=2.0)


def load_electrical_asset_profile(path: Path = ASSET_PROFILE_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"reference_status": "PROFILE_NOT_FOUND"}
    try:
        import yaml
    except ImportError:
        return {"reference_status": "YAML_NOT_AVAILABLE"}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalize_detections(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for detection in detections:
        label = detection.get("class_name") or detection.get("label") or detection.get("name") or ""
        canonical = normalize_yolo_class_name(str(label))
        bbox = [float(value) for value in detection.get("bbox", [])]
        if len(bbox) != 4:
            continue
        normalized.append(
            {
                **detection,
                "class_name": canonical,
                "original_class_name": label,
                "bbox": bbox,
                "confidence": float(detection.get("confidence", detection.get("conf", 0.0)) or 0.0),
            }
        )
    return normalized


def measure_from_detections(
    detections: list[dict[str, Any]],
    *,
    asset_profile: dict[str, Any] | None = None,
    point_id: str = "",
    stabilize: bool = True,
) -> dict[str, Any]:
    asset_profile = asset_profile or load_electrical_asset_profile()
    normalized = normalize_detections(detections)
    groups = _group(normalized)
    tree = _best(groups.get("pohon_sono", []) + groups.get("vegetation_other", []))
    pole = _best(groups.get("struktur_penyangga", []))
    conductors = groups.get("konduktor", [])
    spans = groups.get("span", [])
    transformer = _best(groups.get("trafo", []))

    if tree is None:
        return _not_ready("TREE_NOT_DETECTED", normalized, "Vegetation/tree detection is required.")
    if pole is None:
        return _not_ready("INSUFFICIENT_REFERENCE_OBJECT", normalized, "Pole/struktur_penyangga is required for pixel-to-meter scaling.")

    pole_height_ref = asset_profile.get("pole_height_reference_m")
    scale = meter_per_pixel(pole_height_ref, bbox_height(pole["bbox"]))
    if scale["meter_per_pixel"] is None:
        return {
            **_not_ready(scale["status"], normalized, "Set pole_height_reference_m from PLN/lapangan before auto measurement."),
            "reference_status": asset_profile.get("reference_status", "CONFIG_NEEDS_FIELD_CONFIRMATION"),
        }
    meter_px = float(scale["meter_per_pixel"])
    pole_base_y = bbox_bottom_y(pole["bbox"])
    tree_top_height = height_above_reference_base(bbox_top_y(tree["bbox"]), pole_base_y, meter_px)
    tree_height = object_height_from_bbox(tree["bbox"], meter_px)
    pole_height = object_height_from_bbox(pole["bbox"], meter_px)

    cable_height = None
    clearance_to_cable = None
    if conductors:
        cable = _best(conductors)
        _, cable_y = bbox_center(cable["bbox"])
        cable_height = height_above_reference_base(cable_y, pole_base_y, meter_px)
        clearance_to_cable = round(cable_height - tree_top_height, 3)

    span_height = None
    clearance_to_span = None
    span_status = "SPAN_NOT_DETECTED"
    span_candidates = spans or conductors
    if span_candidates:
        points = span_points_from_detections(span_candidates)
        span_result = estimate_span_lowest_point(points)
        span_status = span_result["status"]
        if span_result["lowest_point"]:
            span_height = height_above_reference_base(span_result["lowest_point"]["y"], pole_base_y, meter_px)
            clearance_to_span = round(span_height - tree_top_height, 3)

    transformer_height = None
    clearance_to_transformer = None
    transformer_status = "TRANSFORMER_NOT_DETECTED"
    if transformer is not None:
        transformer_status = "TRANSFORMER_DETECTED"
        _, trafo_y = bbox_center(transformer["bbox"])
        transformer_height = height_above_reference_base(trafo_y, pole_base_y, meter_px)
        clearance_to_transformer = round(transformer_height - tree_top_height, 3)

    selected = _select_clearance(
        {
            "cable": clearance_to_cable,
            "span": clearance_to_span,
            "transformer": clearance_to_transformer,
        }
    )
    if selected["selected_clearance_m"] is None:
        return {
            **_not_ready("HAZARD_TARGET_NOT_DETECTED", normalized, "Conductor/span/transformer target is required."),
            "tree_height_m": tree_height,
            "pole_height_m": pole_height,
            "span_status": span_status,
            "transformer_status": transformer_status,
        }

    action = classify_eta_action(selected["selected_clearance_m"], None)
    stabilization = _STABILIZER.update(selected["selected_clearance_m"], action["risk_priority"]) if stabilize else {"status": "RAW_DETECTION"}
    return {
        "measurement_status": "AUTO_MEASUREMENT_READY",
        "model_status": "MODEL_READY_UNVALIDATED_OR_MOCK",
        "point_id": point_id,
        "detected_objects": _detected_summary(normalized),
        "tree_height_m": tree_height,
        "pole_height_m": pole_height,
        "cable_height_m": cable_height,
        "span_lowest_point_height_m": span_height,
        "transformer_height_m": transformer_height,
        "clearance_to_cable_m": clearance_to_cable,
        "clearance_to_span_m": clearance_to_span,
        "clearance_to_transformer_m": clearance_to_transformer,
        "selected_clearance_m": selected["selected_clearance_m"],
        "selected_hazard_target": selected["selected_hazard_target"],
        "measurement_confidence": _confidence(normalized),
        "stabilization_status": stabilization["status"],
        "stabilized_clearance_m": stabilization.get("stabilized_clearance_m"),
        "span_status": span_status,
        "transformer_status": transformer_status,
        "reason": "Auto measurement from detections using pole reference scale. No accuracy claim.",
        "not_accuracy_claim": True,
    }


def run_auto_measurement_for_image(
    image_path: str | Path | None,
    *,
    point_id: str = "",
    detections: list[dict[str, Any]] | None = None,
    asset_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if detections is not None:
        return measure_from_detections(detections, asset_profile=asset_profile, point_id=point_id)
    model = resolve_yolo_model()
    if model["status"] != "MODEL_READY_UNVALIDATED":
        return {
            "measurement_status": "AUTO_MEASUREMENT_NOT_READY",
            "model_status": model["status"],
            "detected_objects": [],
            "selected_clearance_m": None,
            "selected_hazard_target": "unknown",
            "measurement_confidence": "LOW",
            "reason": model["reason"],
            "image_path": str(image_path) if image_path else "",
            "not_accuracy_claim": True,
        }
    return {
        "measurement_status": "AUTO_MEASUREMENT_NOT_READY",
        "model_status": "MODEL_READY_UNVALIDATED",
        "detected_objects": [],
        "selected_clearance_m": None,
        "selected_hazard_target": "unknown",
        "measurement_confidence": "LOW",
        "reason": "YOLO runtime adapter is prepared, but live inference is not executed in Phase 14 validation.",
        "image_path": str(image_path) if image_path else "",
        "not_accuracy_claim": True,
    }


def _group(detections: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for detection in detections:
        groups.setdefault(detection["class_name"], []).append(detection)
    return groups


def _best(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    return max(items, key=lambda item: item.get("confidence", 0.0))


def _not_ready(status: str, detections: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    return {
        "measurement_status": status,
        "model_status": "MODEL_READY_UNVALIDATED_OR_MOCK",
        "detected_objects": _detected_summary(detections),
        "selected_clearance_m": None,
        "selected_hazard_target": "unknown",
        "measurement_confidence": "LOW",
        "reason": reason,
        "not_accuracy_claim": True,
    }


def _detected_summary(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"class_name": item["class_name"], "bbox": item["bbox"], "confidence": item.get("confidence", 0.0)} for item in detections]


def _select_clearance(values: dict[str, float | None]) -> dict[str, Any]:
    available = {key: value for key, value in values.items() if value is not None}
    if not available:
        return {"selected_hazard_target": "unknown", "selected_clearance_m": None}
    target, clearance = min(available.items(), key=lambda item: item[1])
    return {"selected_hazard_target": target, "selected_clearance_m": clearance}


def _confidence(detections: list[dict[str, Any]]) -> str:
    if not detections:
        return "LOW"
    avg = sum(float(item.get("confidence", 0.0)) for item in detections) / len(detections)
    if avg >= 0.7:
        return "MEDIUM"
    return "LOW"
