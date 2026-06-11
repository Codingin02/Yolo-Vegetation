"""Python geometry engine for Plan C snapshot results."""

from __future__ import annotations

from typing import Any

DEFAULT_GEOMETRY_PARAMETERS = {
    "pole_height_min_m": 10.5,
    "pole_height_default_m": 11.0,
    "pole_height_max_m": 12.0,
    "vegetation_clearance_threshold_m": 3.0,
    "gps_accuracy_warning_m": 20.0,
    "manual_distance_override_allowed": True,
}


def compute_plan_c_geometry(
    detections: list[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
    manual_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = metadata or {}
    manual_inputs = manual_inputs or {}
    manual_clearance = _to_float(manual_inputs.get("manual_clearance_m"))
    manual_tree_height = _to_float(manual_inputs.get("manual_tree_height_m"))
    manual_distance = _to_float(manual_inputs.get("manual_distance_m"))
    threshold = DEFAULT_GEOMETRY_PARAMETERS["vegetation_clearance_threshold_m"]

    if manual_clearance is not None:
        return {
            "status": "GEOMETRY_READY_MANUAL_OPERATOR_INPUT",
            "geometry_status": "GEOMETRY_READY_MANUAL_OPERATOR_INPUT",
            "measurement_source": "manual_operator_input",
            "clearance_estimate_m": round(manual_clearance, 3),
            "tree_height_estimate_m": round(manual_tree_height, 3) if manual_tree_height is not None else None,
            "manual_distance_m": round(manual_distance, 3) if manual_distance is not None else None,
            "risk_status": classify_risk_status(manual_clearance, threshold_m=threshold),
            "manual_review_required": False,
            "not_final_pln_measurement": True,
            "parameters": DEFAULT_GEOMETRY_PARAMETERS,
            "warnings": ["Manual input bersifat provisional dan bukan pengganti pengukuran manual PLN."],
        }

    grouped = _largest_by_class(detections)
    missing = [name for name in ["pohon_sono", "konduktor", "struktur_penyangga"] if name not in grouped]
    if missing:
        return _insufficient_geometry(missing)

    structure_box = grouped["struktur_penyangga"].get("bbox_xyxy") or []
    tree_box = grouped["pohon_sono"].get("bbox_xyxy") or []
    conductor_box = grouped["konduktor"].get("bbox_xyxy") or []
    if len(structure_box) != 4 or len(tree_box) != 4 or len(conductor_box) != 4:
        return _insufficient_geometry(["bbox_incomplete"])

    structure_height_px = abs(float(structure_box[3]) - float(structure_box[1]))
    tree_height_px = abs(float(tree_box[3]) - float(tree_box[1]))
    if structure_height_px <= 0 or tree_height_px <= 0:
        return _insufficient_geometry(["bbox_scale_invalid"])

    meter_per_px = DEFAULT_GEOMETRY_PARAMETERS["pole_height_default_m"] / structure_height_px
    tree_height_m = tree_height_px * meter_per_px
    tree_top_y = float(tree_box[1])
    conductor_center_y = (float(conductor_box[1]) + float(conductor_box[3])) / 2
    clearance_m = max((conductor_center_y - tree_top_y) * meter_per_px, 0.0)

    return {
        "status": "GEOMETRY_READY_PROVISIONAL",
        "geometry_status": "GEOMETRY_READY_PROVISIONAL",
        "measurement_source": "yolo_bbox_scaled_by_structure_proxy",
        "clearance_estimate_m": round(clearance_m, 3),
        "tree_height_estimate_m": round(tree_height_m, 3),
        "risk_status": classify_risk_status(clearance_m, threshold_m=threshold),
        "manual_review_required": True,
        "not_final_pln_measurement": True,
        "parameters": DEFAULT_GEOMETRY_PARAMETERS,
        "warnings": ["Estimasi berbasis bbox snapshot dan tinggi tiang default; validasi manual tetap diperlukan."],
    }


def classify_risk_status(clearance_m: float | None, *, threshold_m: float = 3.0) -> str:
    if clearance_m is None:
        return "DATA_TIDAK_CUKUP"
    if clearance_m <= threshold_m:
        return "PERLU_PEMANGKASAN"
    if clearance_m <= threshold_m + 0.5:
        return "SIAGA"
    if clearance_m <= threshold_m + 1.5:
        return "PANTAU"
    return "AMAN"


def _insufficient_geometry(missing: list[str]) -> dict[str, Any]:
    return {
        "status": "INSUFFICIENT_GEOMETRY_DATA",
        "geometry_status": "INSUFFICIENT_GEOMETRY_DATA",
        "measurement_source": "not_available",
        "missing_inputs": missing,
        "clearance_estimate_m": None,
        "tree_height_estimate_m": None,
        "risk_status": "DATA_TIDAK_CUKUP",
        "manual_review_required": True,
        "parameters": DEFAULT_GEOMETRY_PARAMETERS,
        "warnings": ["Data bbox belum cukup untuk estimasi geometry."],
    }


def _largest_by_class(detections: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for detection in detections:
        class_name = str(detection.get("class_name") or "")
        if class_name not in {"pohon_sono", "konduktor", "struktur_penyangga"}:
            continue
        current_area = _bbox_area(grouped.get(class_name, {}).get("bbox_xyxy"))
        candidate_area = _bbox_area(detection.get("bbox_xyxy"))
        if candidate_area >= current_area:
            grouped[class_name] = detection
    return grouped


def _bbox_area(box: Any) -> float:
    if not isinstance(box, list) or len(box) != 4:
        return 0.0
    return max(float(box[2]) - float(box[0]), 0.0) * max(float(box[3]) - float(box[1]), 0.0)


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
