from __future__ import annotations

from functools import lru_cache
import csv
import json
import math
from typing import Any

import cv2
import numpy as np

from .storage import PROJECT_ROOT


REQUIRED_CLASSES = ("angsana", "konduktor", "struktur_penyangga_sutm")
REQUIRED_CAPTURE_DISTANCE_M = 10.0
CALIBRATION_PATH = PROJECT_ROOT / "data" / "reference" / "camera_calibration.json"
SUPPORT_REFERENCE_PATH = PROJECT_ROOT / "data" / "reference" / "pln_poles.csv"
CLEARANCE_REFERENCE_PATH = PROJECT_ROOT / "data" / "reference" / "electrical_clearance.csv"


def resolve_thresholds(
    network_type: Any,
    voltage_kv: Any,
    measurement_basis: Any,
    monitor_threshold_m: Any = None,
    monitor_threshold_source: Any = None,
    *,
    network_policy_accepted: bool = False,
) -> dict[str, Any]:
    network = str(network_type or "").upper().strip()
    voltage = _number(voltage_kv, minimum=0.0)
    basis = str(measurement_basis or "").strip()
    network_references = [
        row for row in _reference_rows(CLEARANCE_REFERENCE_PATH)
        if row["network_type"] == network and _number(row["voltage_kv"]) == voltage
    ]
    reference = next((row for row in network_references if row["clearance_measurement_type"] == basis), None)
    accepted = reference is not None and (
        reference["acceptance"] == "official_standard"
        or network_policy_accepted is True
    )
    action = _number(reference["action_threshold_m"], minimum=0.0) if accepted else None
    monitor = _number(monitor_threshold_m, minimum=0.0)
    monitor_source = str(monitor_threshold_source or "").strip() or None
    if (
        action is None or monitor is None or monitor <= action or monitor_source is None
        or network_policy_accepted is not True
    ):
        monitor = None
    return {
        "status": "configured" if action is not None else (
            "threshold_incompatible" if network_references and reference is None else "threshold_not_configured"
        ),
        "network_type": network or None,
        "voltage_kv": voltage,
        "measurement_basis": basis or None,
        "clearance_measurement_type": basis or None,
        "action_threshold_m": action,
        "monitor_threshold_m": monitor,
        "action_ready": action is not None,
        "ready": action is not None and monitor is not None,
        "source": reference["source_url"] if reference else None,
        "source_id": reference["source_id"] if reference else None,
        "standard_id": reference["standard_id"] if reference else None,
        "standard_version": reference.get("standard_version") if reference else None,
        "monitor_threshold_source": monitor_source if monitor is not None else None,
        "acceptance_required": reference is not None and not accepted,
    }


def configured_thresholds(measurement_basis: str = "nearest") -> dict[str, Any]:
    # Safety policy is local configuration; uploaded calibration/thresholds cannot authorize action.
    profile = _load_calibration() or {}
    return resolve_thresholds(
        profile.get("network_type"), profile.get("voltage_kv"), measurement_basis,
        profile.get("monitor_threshold_m"), profile.get("monitor_threshold_source"),
        network_policy_accepted=profile.get("network_policy_accepted") is True,
    )


def diameter_at_axial_position(spec: dict[str, str], axial_m: float) -> float:
    """Diameter in mm, measured downward from the manufactured support top."""
    length = float(spec["nominal_length_m"])
    if not math.isfinite(axial_m) or not 0 <= axial_m <= length:
        raise ValueError("invalid support axial position")
    top, bottom = float(spec["top_diameter_mm"]), float(spec["bottom_diameter_mm"])
    taper_denominator = float(spec["nominal_taper"].split("/")[1])
    return min(bottom, max(top, top + axial_m * 1000 / taper_denominator))


def validate_support_reference(
    family_value: Any, spec_value: Any, buried_value: Any, standard_installation: bool = False,
) -> tuple[dict[str, str] | None, float | None]:
    family = str(family_value or "unknown").strip()
    spec = str(spec_value or "").strip()
    if family not in {"unknown", "beton_pratekan", "baja"} or (family != "beton_pratekan" and spec):
        raise ValueError("invalid support family or specification")
    record = next((row for row in _reference_rows(SUPPORT_REFERENCE_PATH)
                   if row["support_spec"] == spec and row["support_family"] == family), None)
    if spec and record is None:
        raise ValueError("invalid support specification")
    buried = _number(buried_value, minimum=0.001)
    if buried_value not in (None, "") and buried is None:
        raise ValueError("invalid support buried length")
    if standard_installation and buried is not None:
        raise ValueError("conflicting support burial inputs")
    if standard_installation and record is None:
        raise ValueError("confirmed concrete support specification required")
    if standard_installation and record is not None:
        buried = float(record["nominal_length_m"]) / 6
    if buried is not None and (record is None or buried >= float(record["nominal_length_m"])):
        raise ValueError("invalid support buried length")
    return record, buried


@lru_cache(maxsize=2)
def _reference_rows(path: Any) -> tuple[dict[str, str], ...]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return tuple(csv.DictReader(handle))
    except (OSError, csv.Error):
        return ()


def build_geometry_contract(
    detections: list[dict[str, Any]],
    *,
    image_width: Any = None,
    image_height: Any = None,
    camera_calibration: dict[str, Any] | None = None,
    capture_distance_m: Any = None,
    monitor_threshold_m: Any = None,
    action_threshold_m: Any = None,
    support_family: Any = None,
    support_spec: Any = None,
    support_buried_length_m: Any = None,
    support_standard_installation_confirmed: bool = False,
    support_full_height_confirmed: bool = False,
    tree_base_visible_confirmed: bool = False,
) -> dict[str, Any]:
    width = _positive_int(image_width)
    height = _positive_int(image_height)
    segmented_classes = {
        str(item.get("class_name"))
        for item in detections
        if _valid_polygon(item.get("mask_polygon_xyn"))
    }
    tree_detections = [
        (index, item, _pixel_polygon(item.get("mask_polygon_xyn"), width, height))
        for index, item in enumerate(detections)
        if item.get("class_name") == "angsana" and _valid_polygon(item.get("mask_polygon_xyn"))
    ]
    conductor_detections = [
        (index, item, _pixel_polygon(item.get("mask_polygon_xyn"), width, height))
        for index, item in enumerate(detections)
        if item.get("class_name") == "konduktor" and _valid_polygon(item.get("mask_polygon_xyn"))
    ]
    tree_detections = [item for item in tree_detections if item[2] is not None]
    conductor_detections = [item for item in conductor_detections if item[2] is not None]
    support_detections = [
        (index, item, _pixel_polygon(item.get("mask_polygon_xyn"), width, height))
        for index, item in enumerate(detections)
        if item.get("class_name") == "struktur_penyangga_sutm" and _valid_polygon(item.get("mask_polygon_xyn"))
    ]
    support_detections = [item for item in support_detections if item[2] is not None]

    trusted_profile = _load_calibration() or {}
    profile = trusted_profile if _valid_calibration(trusted_profile) else (
        camera_calibration if isinstance(camera_calibration, dict) else trusted_profile
    )
    calibration = _scaled_calibration(profile, width, height)
    calibration_ready = calibration is not None
    distance = _number(capture_distance_m, minimum=0.0)
    if distance is None and isinstance(profile, dict):
        distance = _number(profile.get("capture_distance_m"), minimum=0.0)
    capture_ready = distance is not None and math.isclose(distance, REQUIRED_CAPTURE_DISTANCE_M, abs_tol=1e-6)
    thresholds = configured_thresholds()
    segmentation_ready = all(name in segmented_classes for name in ("angsana", "konduktor"))
    if support_family is not None:
        family, spec = support_family, support_spec
        buried_input = support_buried_length_m
        standard_installation = support_standard_installation_confirmed is True
    else:
        family, spec = trusted_profile.get("support_family"), trusted_profile.get("support_spec")
        buried_input = trusted_profile.get("support_buried_length_m")
        standard_installation = trusted_profile.get("support_standard_installation_confirmed") is True
    support_record, buried_depth = validate_support_reference(family, spec, buried_input, standard_installation)
    nominal_length = float(support_record["nominal_length_m"]) if support_record else None
    visible_height = nominal_length - buried_depth if nominal_length is not None and buried_depth is not None else None

    trees = [
        _tree_geometry(
            index,
            detection,
            polygon,
            conductor_detections,
            support_detections,
            calibration,
            distance if capture_ready else None,
            thresholds,
            width,
            height,
            trusted_profile,
            support_record,
            visible_height,
            support_full_height_confirmed,
            tree_base_visible_confirmed,
        )
        for index, detection, polygon in tree_detections
    ]
    primary = max(trees, key=lambda item: float(item.get("confidence") or 0), default=None)

    if "angsana" not in segmented_classes:
        measurement_status = "insufficient_data"
    elif "konduktor" not in segmented_classes:
        measurement_status = "conductor_not_detected"
    elif width is None or height is None:
        measurement_status = "insufficient_data"
    elif not calibration_ready:
        measurement_status = "uncalibrated_device"
    elif not capture_ready:
        measurement_status = "capture_protocol_required"
    else:
        measurement_status = "ok"
    if not segmentation_ready:
        status = "segmentation_required"
    elif not calibration_ready:
        status = "camera_calibration_required"
    elif not capture_ready:
        status = "capture_protocol_required"
    else:
        status = "inputs_ready"

    return {
        "status": status,
        "measurement_status": primary.get("measurement_status") if primary else measurement_status,
        "segmentation_ready": segmentation_ready,
        "required_classes": list(REQUIRED_CLASSES),
        "camera_calibration_ready": calibration_ready,
        "calibration": {
            "status": "ready" if calibration_ready else "uncalibrated_device",
            "ready": calibration_ready,
            "profile": "data/reference/camera_calibration.json",
        },
        "capture": {
            "required_distance_m": REQUIRED_CAPTURE_DISTANCE_M,
            "distance_m": distance,
            "ready": capture_ready,
            "zoom": "1x",
            "distance_reference": "camera_to_tree_base",
        },
        "support_reference": {
            "support_family": str(family or "unknown"),
            "support_spec": spec or None,
            "nominal_length_m": nominal_length,
            "buried_length_m": buried_depth,
            "visible_height_m": round(visible_height, 2) if visible_height is not None else None,
            "top_diameter_mm": float(support_record["top_diameter_mm"]) if support_record else None,
            "groundline_diameter_mm": round(diameter_at_axial_position(support_record, visible_height), 1) if visible_height is not None else None,
            "bottom_diameter_mm": float(support_record["bottom_diameter_mm"]) if support_record else None,
            "working_load_daN": int(support_record["working_load_daN"]) if support_record else None,
            "nominal_taper": support_record["nominal_taper"] if support_record else None,
            "mark_height_above_ground_m": float(support_record["mark_height_above_ground_m"]) if support_record else None,
            "standard_installation_confirmed": standard_installation,
            "support_range_m": primary["support_range_m"] if primary else None,
            "support_range_confidence": primary["support_range_confidence"] if primary else "unavailable",
            "status": primary["support_reference_status"] if primary else (
                "support_spec_unknown" if support_record is None else
                "insufficient_installation_data" if visible_height is None else "support_not_detected_or_clipped"
            ),
            "standard_id": support_record["standard_id"] if support_record else None,
            "standard_version": support_record["standard_version"] if support_record else None,
            "source": support_record["source_url"] if support_record else None,
        },
        "thresholds": thresholds,
        "trees": trees,
        "tree_track_id": primary.get("track_id") if primary else None,
        "measurements": primary.get("measurements") if primary else _empty_measurements(),
        "risk_bands": primary.get("risk_bands") if primary else [],
        "risk_status": primary.get("risk_status") if primary else (
            "not_computed" if width is None or height is None else measurement_status
        ),
    }


def _tree_geometry(
    detection_index: int,
    detection: dict[str, Any],
    tree: np.ndarray,
    conductors: list[tuple[int, dict[str, Any], np.ndarray]],
    supports: list[tuple[int, dict[str, Any], np.ndarray]],
    calibration: dict[str, Any] | None,
    distance: float | None,
    thresholds: dict[str, Any],
    width: int,
    height: int,
    profile: dict[str, Any],
    support_record: dict[str, str] | None,
    support_visible_height: float | None,
    support_full_height_confirmed: bool,
    tree_base_visible_confirmed: bool,
) -> dict[str, Any]:
    tree_top = _edge_point(tree, axis=1, minimum=True)
    bottom = _edge_point(tree, axis=1, minimum=False)
    tree_base = bottom if tree_base_visible_confirmed and bottom[1] < height - 2 else None
    crown_left = _edge_point(tree, axis=0, minimum=True)
    crown_right = _edge_point(tree, axis=0, minimum=False)
    crown_area_px = abs(float(cv2.contourArea(tree.astype(np.float32))))
    nearest = _nearest_conductor(tree, conductors)
    nearest_point = nearest[3] if nearest else None
    clearance_px = float(nearest[0]) if nearest else None
    conductor = nearest[2] if nearest else None
    segment = nearest[4] if nearest else None

    metrics: dict[str, Any] = {
        "tree_height_camera_m": None,
        "tree_height_support_reference_m": None,
        "tree_height_m": None,
        "crown_width_m": None,
        "crown_area_m2": None,
        "clearance_m": None,
    }
    clearance_m_exact = None
    camera_height = None
    support_height = None
    plane_depth = None
    if calibration is not None and distance is not None and tree_base is not None:
        base_ray = _plane_points(np.asarray([tree_base]), calibration, 1.0)[0]
        # Ten metres is slant range to the base, not optical-axis depth.
        plane_depth = distance / math.sqrt(1.0 + float(base_ray @ base_ray))
        tree_plane = _plane_points(tree, calibration, plane_depth)
        top_plane, base_plane = _plane_points(np.asarray([tree_top, tree_base]), calibration, plane_depth)
        camera_height = abs(float(base_plane[1] - top_plane[1]))
        if profile.get("level_camera_confirmed") is True:
            metrics["tree_height_camera_m"] = round(camera_height, 1)
            metrics["tree_height_m"] = round(camera_height, 1)
        else:
            camera_height = None
        left_plane = _plane_points(np.asarray([crown_left]), calibration, plane_depth)[0]
        right_plane = _plane_points(np.asarray([crown_right]), calibration, plane_depth)[0]
        metrics["crown_width_m"] = round(abs(float(right_plane[0] - left_plane[0])), 1)
        metrics["crown_area_m2"] = round(abs(float(cv2.contourArea(tree_plane.astype(np.float32)))), 1)
        metric_candidates = []
        for conductor_index, conductor_detection, conductor_polygon in conductors:
            conductor_plane = _plane_points(conductor_polygon, calibration, plane_depth)
            metric_distance = _nearest_polygons(tree_plane, conductor_plane)[0]
            metric_candidates.append((metric_distance, conductor_index, conductor_detection, conductor_polygon))
        if metric_candidates:
            metric_best = min(metric_candidates, key=lambda item: item[0])
            clearance_m_exact = float(metric_best[0])
            metrics["clearance_m"] = round(clearance_m_exact, 1)
            # Anisotropic calibration can select a different nearest conductor than raw pixels.
            nearest = _nearest_conductor(tree, [(metric_best[1], metric_best[2], metric_best[3])])
            conductor, nearest_point, segment = nearest[2:5]
            clearance_px = float(nearest[0])

    support = max((item for item in supports
                if not _touches_frame(item[2], width, height)
                and float(item[1].get("confidence") or 0) >= 0.7),
               key=lambda item: float(item[1].get("confidence") or 0), default=None)
    level_camera = profile.get("level_camera_confirmed") is True
    common_depth = profile.get("common_depth_confirmed") is True
    support_top = _edge_point(support[2], axis=1, minimum=True) if support else None
    support_base = _edge_point(support[2], axis=1, minimum=False) if support else None
    support_range, support_range_confidence = (None, "unavailable")
    if support_record is None:
        support_status = "support_spec_unknown"
    elif support_visible_height is None:
        support_status = "insufficient_installation_data"
    elif support is None or not support_full_height_confirmed:
        support_status = "support_not_detected_or_clipped"
    elif calibration is None:
        support_status = "incomparable_geometry"
    else:
        support_range, support_range_confidence = _support_range(
            support[2], support_record, support_visible_height, calibration
        )
        support_status = "range_ready" if support_range is not None else "support_range_unreliable"
        if (support_range is not None and tree_base is not None and plane_depth is not None
                and common_depth and abs(support_range - plane_depth) / plane_depth <= 0.2):
            rays = _plane_points(np.asarray([tree_top, tree_base, support_top, support_base]), calibration, 1.0)
            support_direction = rays[3] - rays[2]
            support_span = float(np.linalg.norm(support_direction))
            tree_span = abs(float(np.dot(rays[1] - rays[0], support_direction / support_span))) if support_span > 0 else 0
            if support_span > 0:
                support_height = support_visible_height * tree_span / support_span * plane_depth / support_range
                metrics["tree_height_support_reference_m"] = round(support_height, 1)
                support_status = "projective_crosscheck"
        elif support_range is not None and tree_base is not None and plane_depth is not None:
            support_status = "incomparable_depth"

    fusion_status = "camera_only" if camera_height is not None else "unavailable"
    disagreement = False
    if camera_height is not None and support_height is not None:
        disagreement = abs(camera_height - support_height) / max(camera_height, support_height, 1e-9) > 0.20
        fusion_status = "disagreement" if disagreement else "consistent_estimates"
        if not disagreement:
            metrics["tree_height_m"] = round((camera_height + support_height) / 2, 1)
    elif support_height is not None:
        metrics["tree_height_m"] = round(support_height, 1)
        fusion_status = "support_only_low_confidence"

    uncertainty = ["single_view_planar_approximation", "segmentation_boundary_uncertainty"]
    if calibration is None:
        uncertainty.append("camera_calibration_missing")
    if distance is None:
        uncertainty.append("capture_distance_not_verified")
    if tree_base is None:
        uncertainty.append("tree_base_not_visible")
    if _touches_frame(tree, width, height):
        uncertainty.append("partial_occlusion_or_frame_clipping")
    if float(detection.get("confidence") or 0) < 0.7:
        uncertainty.append("angsana_segmentation_confidence")
    if nearest and float(nearest[1].get("confidence") or 0) < 0.7:
        uncertainty.append("conductor_segmentation_confidence")
    if not level_camera:
        uncertainty.append("camera_orientation_unverified")
    if not common_depth:
        uncertainty.append("tree_conductor_depth_relation_unverified")
    if support_record is not None and support_status in {"insufficient_installation_data", "support_range_unreliable", "incomparable_depth"}:
        uncertainty.append("support_reference_unreliable")
    if disagreement:
        uncertainty.append("camera_support_height_disagreement")
    reprojection_error = _number(profile.get("reprojection_error_px"), minimum=0.0)
    positioning_tolerance = _number(profile.get("capture_distance_tolerance_m"), minimum=0.0)
    boundary_tolerance = _number(profile.get("segmentation_boundary_tolerance_px"), minimum=0.0)
    if reprojection_error is None:
        uncertainty.append("calibration_uncertainty_unquantified")
    if positioning_tolerance is None:
        uncertainty.append("capture_distance_tolerance_unknown")
    clearance_range = None
    if (clearance_m_exact is not None and plane_depth is not None and distance is not None
            and reprojection_error is not None and positioning_tolerance is not None
            and boundary_tolerance is not None):
        tolerance = (clearance_m_exact * positioning_tolerance / distance
                     + 2 * plane_depth * (boundary_tolerance + reprojection_error)
                     / min(calibration["fx"], calibration["fy"]))
        clearance_range = [max(0.0, clearance_m_exact - tolerance), clearance_m_exact + tolerance]
        uncertainty.append("clearance_range_is_planar_tolerance_bound_not_probability_interval")

    if conductor is None:
        measurement_status = "conductor_not_detected"
    elif calibration is None:
        measurement_status = "uncalibrated_device"
    elif distance is None:
        measurement_status = "capture_protocol_required"
    elif tree_base is None:
        measurement_status = "insufficient_data"
    else:
        measurement_status = "ok"
    unreliable_boundary = (
        tree_base is None
        or _touches_frame(tree, width, height)
        or float(detection.get("confidence") or 0) < 0.7
        or (nearest is not None and float(nearest[1].get("confidence") or 0) < 0.7)
        or not level_camera
        or not common_depth
        or disagreement
        or "calibration_uncertainty_unquantified" in uncertainty
        or "capture_distance_tolerance_unknown" in uncertainty
        or not _valid_calibration(profile)
        or (reprojection_error is not None and reprojection_error > 2.0)
        or (positioning_tolerance is not None and positioning_tolerance > 0.5)
    )
    # A single calibrated view at an assumed common depth is approximate, so confidence is never high.
    measurement_confidence = "low" if measurement_status != "ok" or unreliable_boundary else "medium"

    if measurement_status != "ok":
        risk_status = measurement_status
    elif not thresholds["action_ready"]:
        risk_status = thresholds["status"]
    elif measurement_confidence == "low":
        risk_status = "geometry_unreliable"
    elif clearance_m_exact <= thresholds["action_threshold_m"]:
        risk_status = "TEBANG"
    elif thresholds["monitor_threshold_m"] is not None and clearance_m_exact <= thresholds["monitor_threshold_m"]:
        risk_status = "PANTAU"
    else:
        risk_status = "AMAN"

    risk_bands = []
    if (
        thresholds["ready"]
        and measurement_confidence != "low"
        and calibration is not None
        and plane_depth is not None
        and segment is not None
        and conductor is not None
    ):
        risk_bands = _risk_bands(
            segment,
            conductor,
            nearest[6],
            thresholds["action_threshold_m"],
            thresholds["monitor_threshold_m"],
            calibration,
            plane_depth,
            width,
            height,
        )

    measurements = {
        "tree_top_px": _point(tree_top),
        "tree_base_px": _point(tree_base),
        "tree_height_px": round(float(tree_base[1] - tree_top[1]), 2) if tree_base is not None else None,
        "crown_left_px": _point(crown_left),
        "crown_right_px": _point(crown_right),
        "crown_width_px": round(float(crown_right[0] - crown_left[0]), 2),
        "visible_crown_area_px": round(crown_area_px, 2),
        "crown_area_px": round(crown_area_px, 2),
        "nearest_conductor_point_px": _point(nearest_point),
        "conductor_nearest_point_px": _point(nearest_point),
        "nearest_crown_point_px": _point(nearest[6]) if nearest else None,
        "clearance_px": round(clearance_px, 2) if clearance_px is not None else None,
        **metrics,
        "clearance_unrounded_m": clearance_m_exact,
        "clearance_range_m": clearance_range,
        "measurement_basis": "nearest",
        "clearance_measurement_type": "nearest",
        "measurement_method": "calibrated_camera_planar_mask_nearest" if clearance_m_exact is not None else "segmentation_mask_nearest_pixels",
        "geometry_confidence": measurement_confidence,
        "height_fusion_status": fusion_status,
        "tree_age_years": None,
        "measurement_confidence": measurement_confidence,
        "measurement_uncertainty": uncertainty,
    }
    return {
        "detection_index": detection_index,
        "track_id": detection.get("track_id"),
        "confidence": detection.get("confidence"),
        "measurement_status": measurement_status,
        "measurements": measurements,
        "conductor_detection_index": nearest[5] if nearest else None,
        "conductor_track_id": nearest[1].get("track_id") if nearest else None,
        "conductor_segment_px": [_point(point) for point in segment] if segment is not None else None,
        "support_reference_status": support_status,
        "support_top_px": _point(support_top),
        "support_base_px": _point(support_base),
        "support_track_id": support[1].get("track_id") if support else None,
        "support_range_m": round(support_range, 1) if support_range is not None else None,
        "support_range_confidence": support_range_confidence,
        "thresholds": thresholds,
        "risk_status": risk_status,
        "risk_bands": risk_bands,
    }


def _nearest_conductor(
    tree: np.ndarray,
    conductors: list[tuple[int, dict[str, Any], np.ndarray]],
) -> tuple[float, dict[str, Any], np.ndarray, np.ndarray, np.ndarray, int, np.ndarray] | None:
    best = None
    for index, detection, polygon in conductors:
        distance, crown_point, nearest, segment = _nearest_polygons(tree, polygon)
        candidate = (float(distance), detection, polygon, nearest, segment, index, crown_point)
        if best is None or candidate[0] < best[0]:
            best = candidate
    return best


def _support_range(
    polygon: np.ndarray, spec: dict[str, str], visible_height_m: float, calibration: dict[str, Any],
) -> tuple[float | None, str]:
    points = cv2.undistortPoints(
        polygon.reshape(-1, 1, 2).astype(np.float64), calibration["matrix"],
        calibration["distortion"], P=calibration["matrix"],
    ).reshape(-1, 2)
    top = _edge_point(points, axis=1, minimum=True)
    base = _edge_point(points, axis=1, minimum=False)
    axis = base - top
    axis_length = float(np.linalg.norm(axis))
    if axis_length < 40 or visible_height_m <= 0:
        return None, "low"
    axis /= axis_length
    perpendicular = np.asarray([-axis[1], axis[0]])
    ends = np.roll(points, -1, axis=0)
    ranges = []
    focal = math.hypot(calibration["fx"] * perpendicular[0], calibration["fy"] * perpendicular[1])
    for fraction in (0.2, 0.4, 0.6, 0.8):
        center = top + fraction * (base - top)
        before = (points - center) @ axis
        after = (ends - center) @ axis
        crossing = (before <= 0) != (after <= 0)
        if crossing.sum() < 2:
            continue
        t = -before[crossing] / (after[crossing] - before[crossing])
        positions = points[crossing] + t[:, None] * (ends[crossing] - points[crossing])
        projections = positions @ perpendicular
        width_px = float(np.ptp(projections))
        if width_px < 3:
            continue
        diameter_m = diameter_at_axial_position(spec, fraction * visible_height_m) / 1000
        ranges.append(focal * diameter_m / width_px)
    if len(ranges) < 3:
        return None, "low"
    median_range = float(np.median(ranges))
    if not 2 <= median_range <= 100 or max(abs(value - median_range) / median_range for value in ranges) > 0.18:
        return None, "low"
    return median_range, "medium"


def _nearest_polygons(first: np.ndarray, second: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    first_contour, second_contour = first.astype(np.float32), second.astype(np.float32)
    for point in first:
        if cv2.pointPolygonTest(second_contour, tuple(map(float, point)), False) >= 0:
            return 0.0, point, point, _nearest_point_on_polyline(point, second)[2]
    for point in second:
        if cv2.pointPolygonTest(first_contour, tuple(map(float, point)), False) >= 0:
            return 0.0, point, point, _nearest_point_on_polyline(point, second)[2]
    best = (math.inf, first[0], second[0], np.asarray([second[0], second[1]]))
    ends = np.roll(second, -1, axis=0)
    deltas = ends - second
    # ponytail: contour edge pairs are O(n*m); simplify dense contours if this ever dominates inference.
    for start, end in zip(first, np.roll(first, -1, axis=0)):
        direction = end - start
        offsets = second - start
        denominator = direction[0] * deltas[:, 1] - direction[1] * deltas[:, 0]
        nonparallel = np.abs(denominator) > 1e-12
        t = np.divide(offsets[:, 0] * deltas[:, 1] - offsets[:, 1] * deltas[:, 0],
                      denominator, out=np.full(len(second), np.inf), where=nonparallel)
        u = np.divide(offsets[:, 0] * direction[1] - offsets[:, 1] * direction[0],
                      denominator, out=np.full(len(second), np.inf), where=nonparallel)
        crossing = np.flatnonzero(nonparallel & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1))
        if crossing.size:
            index = int(crossing[0])
            point = start + t[index] * direction
            return 0.0, point, point, np.asarray([second[index], ends[index]])
        distance, point, segment, _ = _nearest_point_on_polyline(start, second)
        if distance < best[0]:
            best = (distance, start, point, segment)
    for index, point in enumerate(second):
        distance, nearest, _, _ = _nearest_point_on_polyline(point, first)
        if distance < best[0]:
            best = (distance, nearest, point, np.asarray([second[index], ends[index]]))
    return best


def _nearest_point_on_polyline(point: np.ndarray, polygon: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, float]:
    ends = np.roll(polygon, -1, axis=0)
    delta = ends - polygon
    denominator = np.einsum("ij,ij->i", delta, delta)
    numerator = np.einsum("ij,ij->i", point - polygon, delta)
    t = np.clip(np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0), 0, 1)
    candidates = polygon + t[:, None] * delta
    distances = np.linalg.norm(point - candidates, axis=1)
    index = int(np.argmin(distances))
    return float(distances[index]), candidates[index], np.asarray([polygon[index], ends[index]]), float(t[index])


def _risk_bands(
    nearest_segment: np.ndarray,
    conductor: np.ndarray,
    tree_top: np.ndarray,
    action_m: float,
    monitor_m: float,
    calibration: dict[str, Any],
    distance_m: float,
    width: int,
    height: int,
) -> list[dict[str, Any]]:
    nearest_segment = _plane_points(nearest_segment, calibration, distance_m)
    conductor = _plane_points(conductor, calibration, distance_m)
    tree_top = _plane_points(np.asarray([tree_top]), calibration, distance_m)[0]
    tangent = nearest_segment[1] - nearest_segment[0]
    norm = float(np.linalg.norm(tangent))
    if norm <= 0:
        return []
    tangent /= norm
    nearest = _nearest_point_on_polyline(tree_top, conductor)[1]
    normal = np.asarray([-tangent[1], tangent[0]])
    if float(np.dot(tree_top - nearest, normal)) < 0:
        normal *= -1
    projections = (conductor - nearest) @ tangent
    start = nearest + tangent * float(projections.min())
    end = nearest + tangent * float(projections.max())
    action_edge_start, action_edge_end = start + normal * action_m, end + normal * action_m
    monitor_edge_start, monitor_edge_end = start + normal * monitor_m, end + normal * monitor_m
    return [
        {
            "status": "PANTAU",
            "polygon_xyn": _normalized_points(
                _project_plane(np.asarray([action_edge_start, action_edge_end, monitor_edge_end, monitor_edge_start]),
                               calibration, distance_m), width, height
            ),
        },
        {
            "status": "TEBANG",
            "polygon_xyn": _normalized_points(
                _project_plane(np.asarray([start, end, action_edge_end, action_edge_start]),
                               calibration, distance_m), width, height
            ),
        },
    ]


def _project_plane(points: np.ndarray, calibration: dict[str, Any], depth_m: float) -> np.ndarray:
    object_points = np.column_stack((points, np.full(len(points), depth_m)))
    projected, _ = cv2.projectPoints(object_points, np.zeros(3), np.zeros(3),
                                    calibration["matrix"], calibration["distortion"])
    return projected.reshape(-1, 2)


def _plane_points(points: np.ndarray, calibration: dict[str, Any], distance_m: float) -> np.ndarray:
    source = np.asarray(points, dtype=np.float64).reshape(-1, 1, 2)
    normalized = cv2.undistortPoints(source, calibration["matrix"], calibration["distortion"]).reshape(-1, 2)
    return normalized * distance_m


def _scaled_calibration(value: Any, width: int | None, height: int | None) -> dict[str, Any] | None:
    if width is None or height is None or not _valid_calibration(value):
        return None
    source_width = int(value["image_width"])
    source_height = int(value["image_height"])
    if not math.isclose(source_width / source_height, width / height, rel_tol=0.02):
        return None
    scale_x, scale_y = width / source_width, height / source_height
    fx, fy = float(value["fx"]) * scale_x, float(value["fy"]) * scale_y
    cx, cy = float(value["cx"]) * scale_x, float(value["cy"]) * scale_y
    distortion = value.get("dist_coeffs", value.get("distortion_coefficients"))
    return {
        "fx": fx,
        "fy": fy,
        "cx": cx,
        "cy": cy,
        "matrix": np.asarray([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=np.float64),
        "distortion": np.asarray(distortion, dtype=np.float64),
    }


@lru_cache(maxsize=1)
def _load_calibration() -> dict[str, Any] | None:
    try:
        value = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None


def _valid_polygon(value: Any) -> bool:
    if not isinstance(value, list) or len(value) < 3:
        return False
    try:
        points = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        return False
    return (
        points.shape == (len(value), 2)
        and np.isfinite(points).all()
        and ((0 <= points) & (points <= 1)).all()
        and abs(float(cv2.contourArea(points.astype(np.float32)))) > 0
    )


def _valid_calibration(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    width = _positive_int(value.get("image_width"))
    height = _positive_int(value.get("image_height"))
    fx = _number(value.get("fx"), minimum=0.0)
    fy = _number(value.get("fy"), minimum=0.0)
    cx = _number(value.get("cx"))
    cy = _number(value.get("cy"))
    capture_distance = _number(value.get("capture_distance_m"), minimum=0.0)
    distortion = value.get("dist_coeffs", value.get("distortion_coefficients"))
    return (
        width is not None
        and height is not None
        and fx is not None
        and fx > 0
        and fy is not None
        and fy > 0
        and cx is not None
        and 0 <= cx < width
        and cy is not None
        and 0 <= cy < height
        and capture_distance is not None
        and math.isclose(capture_distance, REQUIRED_CAPTURE_DISTANCE_M, abs_tol=1e-6)
        and isinstance(distortion, list)
        and len(distortion) in (4, 5, 8, 12, 14)
        and all(_number(coefficient) is not None for coefficient in distortion)
    )


def _pixel_polygon(value: Any, width: int | None, height: int | None) -> np.ndarray | None:
    if width is None or height is None or not _valid_polygon(value):
        return None
    points = np.asarray(value, dtype=np.float64)
    points[:, 0] *= width - 1
    points[:, 1] *= height - 1
    return points


def _edge_point(points: np.ndarray, *, axis: int, minimum: bool) -> np.ndarray:
    edge = float(points[:, axis].min() if minimum else points[:, axis].max())
    tolerance = max(1.0, float(np.ptp(points[:, axis])) * 0.01)
    candidates = points[points[:, axis] <= edge + tolerance] if minimum else points[points[:, axis] >= edge - tolerance]
    other_axis = 1 - axis
    result = np.zeros(2, dtype=np.float64)
    result[axis] = edge
    result[other_axis] = float(candidates[:, other_axis].mean())
    return result


def _touches_frame(points: np.ndarray, width: int, height: int) -> bool:
    return bool(
        (points[:, 0] <= 1).any()
        or (points[:, 1] <= 1).any()
        or (points[:, 0] >= width - 2).any()
        or (points[:, 1] >= height - 2).any()
    )


def _normalized_points(points: np.ndarray, width: int, height: int) -> list[list[float]]:
    normalized = np.asarray(points, dtype=np.float64).copy()
    normalized[:, 0] = np.clip(normalized[:, 0] / max(1, width - 1), 0, 1)
    normalized[:, 1] = np.clip(normalized[:, 1] / max(1, height - 1), 0, 1)
    return [[round(float(x), 6), round(float(y), 6)] for x, y in normalized]


def _point(value: np.ndarray | None) -> list[float] | None:
    return [round(float(value[0]), 2), round(float(value[1]), 2)] if value is not None else None


def _empty_measurements() -> dict[str, Any]:
    return {
        "tree_top_px": None,
        "tree_base_px": None,
        "tree_height_px": None,
        "crown_left_px": None,
        "crown_right_px": None,
        "crown_width_px": None,
        "visible_crown_area_px": None,
        "crown_area_px": None,
        "nearest_conductor_point_px": None,
        "conductor_nearest_point_px": None,
        "nearest_crown_point_px": None,
        "clearance_px": None,
        "tree_height_camera_m": None,
        "tree_height_support_reference_m": None,
        "tree_height_m": None,
        "crown_width_m": None,
        "crown_area_m2": None,
        "clearance_m": None,
        "clearance_unrounded_m": None,
        "clearance_range_m": None,
        "measurement_basis": None,
        "clearance_measurement_type": None,
        "measurement_method": None,
        "geometry_confidence": None,
        "height_fusion_status": None,
        "tree_age_years": None,
        "measurement_confidence": None,
        "measurement_uncertainty": None,
    }


def _positive_int(value: Any) -> int | None:
    number = _number(value, minimum=1.0)
    return int(number) if number is not None and number.is_integer() else None


def _number(value: Any, minimum: float | None = None) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or minimum is not None and number < minimum:
        return None
    return number
