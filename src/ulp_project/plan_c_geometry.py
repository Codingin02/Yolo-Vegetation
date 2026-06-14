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
    manual_structure_height = _to_float(manual_inputs.get("manual_structure_height_m") or manual_inputs.get("structure_height_m"))
    manual_ground_reference_y = _to_float(manual_inputs.get("ground_reference_y") or metadata.get("ground_reference_y"))
    manual_zone = str(manual_inputs.get("manual_zone") or metadata.get("manual_zone") or "").strip().lower()
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
            "conductor_y": None,
            "ground_reference_y": manual_ground_reference_y,
            "ground_reference_status": "GROUND_REFERENCE_MANUAL_OPERATOR_INPUT" if manual_ground_reference_y is not None else "GROUND_REFERENCE_NOT_AVAILABLE",
            "meter_per_pixel": None,
            "meter_per_pixel_source": "manual_operator_input",
            "zone_status": "unavailable",
            "zone_precision": "manual_clearance_only",
            "parameters": DEFAULT_GEOMETRY_PARAMETERS,
            "warnings": ["Manual input bersifat provisional dan bukan pengganti pengukuran manual PLN."],
        }

    grouped = _largest_by_class(detections)
    tree_detection = grouped.get("pohon_sono") or grouped.get("pohon_non_sono")
    conductor_detection = _select_conductor_reference(detections)
    if tree_detection is None:
        return _insufficient_geometry(["pohon_sono"], conductor_validated=False)
    if conductor_detection is None:
        return _single_class_tree_review_geometry(tree_detection, manual_zone=manual_zone)

    structure_detection = grouped.get("struktur_penyangga")
    structure_box = (structure_detection or {}).get("bbox_xyxy") or []
    tree_box = tree_detection.get("bbox_xyxy") or []
    conductor_box = conductor_detection.get("bbox_xyxy") or []
    if len(tree_box) != 4 or len(conductor_box) != 4:
        return _insufficient_geometry(["bbox_incomplete"])

    structure_height_px = abs(float(structure_box[3]) - float(structure_box[1])) if len(structure_box) == 4 else 0.0
    tree_height_px = abs(float(tree_box[3]) - float(tree_box[1]))
    if tree_height_px <= 0:
        return _insufficient_geometry(["bbox_scale_invalid"])

    if structure_height_px <= 0:
        return _geometry_needs_reference_height(["struktur_penyangga_bbox"])

    structure_height_m, structure_height_source = _resolve_structure_height(manual_structure_height, metadata=metadata)
    if structure_height_m is None or structure_height_m <= 0:
        return _geometry_needs_reference_height(["structure_height_m"])

    meter_per_px = structure_height_m / structure_height_px
    scale_status = "SCALE_FROM_STRUCTURE"
    tree_height_m = tree_height_px * meter_per_px
    conductor_center_y = (float(conductor_box[1]) + float(conductor_box[3])) / 2
    ground_reference_y, ground_reference_status = _ground_reference_from_available_bases(
        tree_box,
        structure_box,
        manual_ground_reference_y=manual_ground_reference_y,
    )
    if ground_reference_y is None:
        return _insufficient_geometry(["ground_reference_y"])
    conductor_height_m = max((ground_reference_y - conductor_center_y) * meter_per_px, 0.0)
    zone_fields = _build_zone_fields(
        conductor_y=conductor_center_y,
        meter_per_px=meter_per_px,
        ground_reference_y=ground_reference_y,
        scale_status=scale_status,
    )
    clearance_m = conductor_height_m - tree_height_m
    tree_species_status = str(tree_detection.get("class_name") or "unknown")
    risk_status = classify_risk_status(clearance_m, threshold_m=threshold)
    meter_source = structure_height_source
    conductor_lines = _conductor_lines(detections)
    ground_status = zone_fields.get("ground_reference_status") or ground_reference_status
    if ground_reference_status == "GROUND_REFERENCE_MANUAL_OPERATOR_INPUT" and ground_status != "GROUND_REFERENCE_NOT_ENOUGH_FOR_SAFE_ZONE":
        ground_status = ground_reference_status

    return {
        "status": "GEOMETRY_READY_PROVISIONAL" if scale_status != "APPROXIMATE_VISUAL_ESTIMATE" else "GEOMETRY_READY_APPROXIMATE_VISUAL",
        "geometry_status": "GEOMETRY_READY_PROVISIONAL" if scale_status != "APPROXIMATE_VISUAL_ESTIMATE" else "APPROXIMATE_VISUAL_ESTIMATE",
        "measurement_source": "yolo_compatible_bbox_scaled_by_structure_reference",
        "clearance_estimate_m": round(clearance_m, 3),
        "tree_height_estimate_m": round(tree_height_m, 3),
        "conductor_height_m": round(conductor_height_m, 3),
        "structure_height_m": round(structure_height_m, 3),
        "structure_height_source": structure_height_source,
        "structure_bbox_height_px": round(structure_height_px, 2),
        "tree_bbox_height_px": round(tree_height_px, 2),
        "risk_status": risk_status,
        "manual_review_required": structure_height_source != "STRUCTURE_HEIGHT_MANUAL",
        "tree_species_status": tree_species_status,
        "conductor_status": "tervalidasi",
        "structure_status": "tervalidasi" if structure_height_px > 0 else "tidak tervalidasi",
        "scale_status": scale_status,
        "meter_per_px": round(meter_per_px, 6),
        "meter_per_pixel": round(meter_per_px, 6),
        "meter_per_pixel_source": meter_source,
        "pixels_per_meter": round(1.0 / meter_per_px, 3) if meter_per_px > 0 else None,
        "conductor_y": round(conductor_center_y, 2),
        "conductor_y_px": round(conductor_center_y, 2),
        "conductor_reference_bbox": [round(float(value), 2) for value in conductor_box],
        "conductor_group_count": len(conductor_lines),
        "conductor_lines": conductor_lines,
        "ground_reference_y": round(ground_reference_y, 2) if ground_reference_y is not None else None,
        "ground_reference_status": ground_status,
        **zone_fields,
        "not_final_pln_measurement": True,
        "parameters": DEFAULT_GEOMETRY_PARAMETERS,
        "warnings": ["Estimasi berbasis bbox snapshot; validasi manual PLN tetap diperlukan."],
    }


def classify_risk_status(clearance_m: float | None, *, threshold_m: float = 3.0) -> str:
    if clearance_m is None:
        return "DATA_TIDAK_CUKUP"
    if clearance_m <= threshold_m:
        return "ZONA_TEBANG"
    if clearance_m <= threshold_m + 1.5:
        return "PANTAU"
    return "AMAN"


def _insufficient_geometry(missing: list[str], *, conductor_validated: bool = False) -> dict[str, Any]:
    if "pohon_sono" in missing or "pohon_sono_or_pohon_non_sono" in missing:
        risk_status = "DATA_TIDAK_CUKUP_POHON_TIDAK_TERVALIDASI"
        geometry_status = "DATA_TIDAK_CUKUP_POHON_TIDAK_TERVALIDASI"
    else:
        risk_status = "DATA_TIDAK_CUKUP_GEOMETRY"
        geometry_status = "INSUFFICIENT_GEOMETRY_DATA"
    return {
        "status": "INSUFFICIENT_GEOMETRY_DATA",
        "geometry_status": geometry_status,
        "measurement_source": "not_available",
        "missing_inputs": missing,
        "clearance_estimate_m": None,
        "tree_height_estimate_m": None,
        "conductor_height_m": None,
        "structure_height_m": None,
        "structure_height_source": "STRUCTURE_HEIGHT_UNKNOWN",
        "risk_status": risk_status,
        "manual_review_required": True,
        "tree_species_status": "unknown",
        "conductor_status": "reference/manual only" if not conductor_validated else "tervalidasi",
        "structure_status": "reference/manual only",
        "conductor_required_for_detection": False,
        "zone_status": "unavailable",
        "zone_precision": "unavailable",
        "conductor_y": None,
        "conductor_y_px": None,
        "conductor_group_count": 0,
        "conductor_lines": [],
        "ground_reference_y": None,
        "ground_reference_status": "GROUND_REFERENCE_NOT_AVAILABLE",
        "meter_per_pixel": None,
        "meter_per_pixel_source": "not_available",
        "zone_tebang_y1": None,
        "zone_tebang_y2": None,
        "zone_pantau_y1": None,
        "zone_pantau_y2": None,
        "zone_aman_y1": None,
        "zone_aman_y2": None,
        "parameters": DEFAULT_GEOMETRY_PARAMETERS,
        "warnings": ["Data geometri belum cukup untuk estimasi clearance; review manual diperlukan."],
    }


def _single_class_tree_review_geometry(tree_detection: dict[str, Any], *, manual_zone: str = "") -> dict[str, Any]:
    tree_box = tree_detection.get("bbox_xyxy") or []
    tree_height_px = None
    if isinstance(tree_box, list) and len(tree_box) == 4:
        try:
            tree_height_px = round(abs(float(tree_box[3]) - float(tree_box[1])), 2)
        except (TypeError, ValueError):
            tree_height_px = None
    manual_zone_tebang = manual_zone in {"tebang", "zona_tebang", "zona_tebang_manual_review", "zona_tebang_review"}
    risk_status = "ZONA_TEBANG_MANUAL_REVIEW" if manual_zone_tebang else "POHON_SONO_DETECTED_REVIEW_REQUIRED"
    return {
        "status": "INSUFFICIENT_GEOMETRY_DATA",
        "geometry_status": "INSUFFICIENT_GEOMETRY_DATA",
        "measurement_source": "single_class_pohon_sono_yolov8_without_manual_clearance_reference",
        "reason": "SINGLE_CLASS_TREE_DETECTED_NEEDS_MANUAL_CLEARANCE_REVIEW",
        "missing_inputs": ["manual_clearance_m", "manual_conductor_reference_or_measurement"],
        "clearance_estimate_m": None,
        "tree_height_estimate_m": None,
        "tree_bbox_height_px": tree_height_px,
        "conductor_height_m": None,
        "structure_height_m": None,
        "structure_height_source": "STRUCTURE_HEIGHT_UNKNOWN",
        "risk_status": risk_status,
        "manual_review_required": True,
        "tree_species_status": str(tree_detection.get("class_name") or "pohon_sono"),
        "detected_primary_object": "pohon_sono",
        "conductor_status": "reference/manual only",
        "structure_status": "reference/manual only",
        "conductor_required_for_detection": False,
        "zone_status": "manual_review_required",
        "zone_precision": "manual_review",
        "conductor_y": None,
        "conductor_y_px": None,
        "conductor_group_count": 0,
        "conductor_lines": [],
        "ground_reference_y": None,
        "ground_reference_status": "GROUND_REFERENCE_REQUIRES_MANUAL_REVIEW",
        "meter_per_pixel": None,
        "meter_per_pixel_source": "not_available",
        "zone_tebang_y1": None,
        "zone_tebang_y2": None,
        "zone_pantau_y1": None,
        "zone_pantau_y2": None,
        "zone_aman_y1": None,
        "zone_aman_y2": None,
        "parameters": DEFAULT_GEOMETRY_PARAMETERS,
        "warnings": [
            "YOLOv8 mendeteksi pohon_sono, tetapi clearance tidak dihitung karena referensi konduktor/manual belum tersedia.",
            "Zona tebang/review adalah indikasi operator, bukan keputusan final PLN.",
        ],
    }


def _geometry_needs_reference_height(missing: list[str]) -> dict[str, Any]:
    payload = _insufficient_geometry(missing, conductor_validated=True)
    payload.update(
        {
            "status": "GEOMETRY_NEEDS_REFERENCE_HEIGHT",
            "geometry_status": "GEOMETRY_NEEDS_REFERENCE_HEIGHT",
            "risk_status": "DATA_TIDAK_CUKUP",
            "conductor_status": "tervalidasi",
            "missing_inputs": missing,
            "warnings": ["Struktur penyangga dan tinggi referensi diperlukan untuk skala geometri."],
        }
    )
    return payload


def _resolve_structure_height(manual_structure_height: float | None, *, metadata: dict[str, Any]) -> tuple[float | None, str]:
    if manual_structure_height is not None and manual_structure_height > 0:
        return manual_structure_height, "STRUCTURE_HEIGHT_MANUAL"
    configured = _to_float(metadata.get("structure_height_m") or metadata.get("pole_height_m"))
    if configured is not None and configured > 0:
        return configured, "STRUCTURE_HEIGHT_CONFIG_DEFAULT"
    return DEFAULT_GEOMETRY_PARAMETERS["pole_height_default_m"], "STRUCTURE_HEIGHT_CONFIG_DEFAULT"


def _largest_by_class(detections: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for detection in detections:
        class_name = str(detection.get("class_name") or "")
        if class_name not in {"pohon_sono", "pohon_non_sono", "konduktor", "struktur_penyangga"}:
            continue
        current_area = _bbox_area(grouped.get(class_name, {}).get("bbox_xyxy"))
        candidate_area = _bbox_area(detection.get("bbox_xyxy"))
        if candidate_area >= current_area:
            grouped[class_name] = detection
    return grouped


def _select_conductor_reference(detections: list[dict[str, Any]]) -> dict[str, Any] | None:
    conductors = [item for item in detections if item.get("class_name") == "konduktor" and isinstance(item.get("bbox_xyxy"), list) and len(item.get("bbox_xyxy")) == 4]
    if not conductors:
        return None
    # The lowest visible conductor is the conservative reference for clearance.
    return max(conductors, key=lambda item: (_bbox_center_y(item.get("bbox_xyxy")), float(item.get("confidence") or 0.0)))


def _ground_reference_from_available_bases(
    tree_box: list[Any],
    structure_box: list[Any],
    *,
    manual_ground_reference_y: float | None,
) -> tuple[float | None, str]:
    if manual_ground_reference_y is not None:
        return manual_ground_reference_y, "GROUND_REFERENCE_MANUAL_OPERATOR_INPUT"
    candidates: list[tuple[float, str]] = []
    if isinstance(tree_box, list) and len(tree_box) == 4:
        try:
            candidates.append((float(tree_box[3]), "VEGETATION_BASE_ESTIMATED_FROM_TREE_BBOX"))
        except (TypeError, ValueError):
            pass
    if isinstance(structure_box, list) and len(structure_box) == 4:
        try:
            candidates.append((float(structure_box[3]), "STRUCTURE_BASE_ESTIMATED_FROM_BBOX"))
        except (TypeError, ValueError):
            pass
    if not candidates:
        return None, "GROUND_REFERENCE_NOT_AVAILABLE"
    # Smaller y is conservative for clearance because image y grows downward.
    return min(candidates, key=lambda item: item[0])


def _build_zone_fields(
    *,
    conductor_y: float,
    meter_per_px: float,
    ground_reference_y: float | None,
    scale_status: str,
) -> dict[str, Any]:
    if meter_per_px <= 0 or ground_reference_y is None:
        return {
            "zone_status": "unavailable",
            "zone_precision": "unavailable",
            "ground_reference_status": "GROUND_REFERENCE_NOT_AVAILABLE",
            "zone_tebang_y1": None,
            "zone_tebang_y2": None,
            "zone_pantau_y1": None,
            "zone_pantau_y2": None,
            "zone_aman_y1": None,
            "zone_aman_y2": None,
        }
    px_per_meter = 1.0 / meter_per_px
    tebang_y1 = conductor_y
    tebang_y2_raw = conductor_y + (3.0 * px_per_meter)
    pantau_y1_raw = tebang_y2_raw
    pantau_y2_raw = conductor_y + (6.0 * px_per_meter)
    aman_y1_raw = pantau_y2_raw
    precise = scale_status in {"SCALE_FROM_STRUCTURE", "SCALE_FROM_MANUAL_INPUT"}
    ground_status = "VEGETATION_BASE_ESTIMATED_FROM_TREE_BBOX"
    safe_zone_available = ground_reference_y > aman_y1_raw
    if not safe_zone_available:
        ground_status = "GROUND_REFERENCE_NOT_ENOUGH_FOR_SAFE_ZONE"
    return {
        "zone_status": "precise" if precise else "approximate",
        "zone_precision": "precise" if precise else "approximate",
        "ground_reference_status": ground_status,
        "zone_tebang_y1": round(tebang_y1, 2),
        "zone_tebang_y2": round(min(tebang_y2_raw, ground_reference_y), 2) if ground_reference_y > tebang_y1 else None,
        "zone_pantau_y1": round(pantau_y1_raw, 2) if ground_reference_y > pantau_y1_raw else None,
        "zone_pantau_y2": round(min(pantau_y2_raw, ground_reference_y), 2) if ground_reference_y > pantau_y1_raw else None,
        "zone_aman_y1": round(aman_y1_raw, 2) if safe_zone_available else None,
        "zone_aman_y2": round(ground_reference_y, 2) if safe_zone_available else None,
    }


def _meter_per_pixel_source(scale_status: str) -> str:
    if scale_status == "SCALE_FROM_STRUCTURE":
        return "structure_bbox_pole_height_default"
    if scale_status == "SCALE_FROM_MANUAL_INPUT":
        return "manual_operator_input"
    return "visual_tree_bbox_fallback"


def _conductor_lines(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in detections:
        if item.get("class_name") != "konduktor":
            continue
        bbox = item.get("bbox_xyxy")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            x1, y1, x2, y2 = [float(value) for value in bbox]
        except (TypeError, ValueError):
            continue
        lines.append(
            {
                "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "line_y": round((y1 + y2) / 2.0, 2),
                "confidence": item.get("confidence"),
                "review_status": item.get("review_status"),
            }
        )
    return sorted(lines, key=lambda item: float(item.get("line_y") or 0.0))


def _bbox_center_y(box: Any) -> float:
    if not isinstance(box, list) or len(box) != 4:
        return 0.0
    return (float(box[1]) + float(box[3])) / 2.0


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
