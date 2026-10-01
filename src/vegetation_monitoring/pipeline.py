from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from werkzeug.datastructures import FileStorage

from .detection import TREE_CLASSES, detect_objects
from .geometry import build_geometry_contract
from .growth import predict_growth
from .renderer import render_result
from .storage import (
    append_record,
    as_float,
    load_metadata,
    now_iso,
    read_json,
    relative_path,
    session_file,
    update_metadata,
    write_json,
)


JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png"}
LIGHTING_MODES = {"auto", "normal", "backlight", "low_light"}
_LOGGER = logging.getLogger(__name__)
_LIGHTING_LOCK = threading.Lock()
# ponytail: lighting state follows the existing single active tracker session.
_LIGHTING_STATE: dict[str, Any] = {
    "session": None,
    "gamma": None,
    "preview_brightness": None,
    "correction_strength": None,
    "clahe_strength": None,
    "detections": [],
}


def process_frame(
    frame: np.ndarray,
    payload: dict[str, Any],
    *,
    tracking_session: str | None = None,
    render: bool = True,
) -> tuple[dict[str, Any], np.ndarray]:
    try:
        clearance_m, measurement_source = measurement_values(payload)
        measurement_error = None
    except ValueError as exc:
        clearance_m, measurement_source = None, None
        measurement_error = str(exc)
    growth_stage = str(payload.get("tree_stage") or payload.get("growth_stage") or "").strip() or None
    lighting_mode = str(payload.get("lighting_mode") or "auto").strip().lower()
    if lighting_mode not in LIGHTING_MODES:
        raise ValueError("invalid lighting mode")
    inference_frame, lighting = _adaptive_lighting(frame, lighting_mode, tracking_session)
    detection = detect_objects(inference_frame, tracking_session=tracking_session)
    detections = detection.get("detections") or []
    frame_height, frame_width = frame.shape[:2]
    geometry = build_geometry_contract(
        detections,
        image_width=frame_width,
        image_height=frame_height,
        camera_calibration=payload.get("camera_calibration"),
        capture_distance_m=payload.get("capture_distance_m"),
        monitor_threshold_m=payload.get("monitor_threshold_m"),
        action_threshold_m=payload.get("action_threshold_m"),
        support_family=payload.get("support_family"),
        support_spec=payload.get("support_spec"),
        support_buried_length_m=payload.get("support_buried_length_m"),
        support_standard_installation_confirmed=str(payload.get("support_standard_installation_confirmed") or "").lower() == "true",
        support_full_height_confirmed=str(payload.get("support_full_height_confirmed") or "").lower() == "true",
        tree_base_visible_confirmed=str(payload.get("tree_base_visible_confirmed") or "").lower() == "true",
    )
    if tracking_session:
        with _LIGHTING_LOCK:
            if _LIGHTING_STATE["session"] == tracking_session:
                _LIGHTING_STATE["detections"] = [
                    {
                        "confidence": item.get("confidence"),
                        "bbox_xywhn": item.get("bbox_xywhn"),
                        "track_id": item.get("track_id"),
                    }
                    for item in detections
                ]

    tree_geometry = {
        item["detection_index"]: item
        for item in geometry.get("trees") or []
        if isinstance(item.get("detection_index"), int)
    }
    for index, item in enumerate(detections):
        species = str(item.get("class_name") or "")
        if species in TREE_CLASSES:
            measured = tree_geometry.get(index)
            measurements = (measured.get("measurements") or {}) if measured else {}
            measured_clearance = as_float(measurements.get("clearance_m")) if measurements else None
            item_clearance = measured_clearance if measured_clearance is not None else clearance_m
            if measured:
                item_geometry = {
                    "measurement_status": measured.get("measurement_status"),
                    "measurements": measurements,
                    "risk_status": measured.get("risk_status"),
                    "conductor_track_id": measured.get("conductor_track_id"),
                    "conductor_detection_index": measured.get("conductor_detection_index"),
                    "thresholds": measured.get("thresholds"),
                }
                item["geometry"] = item_geometry
            else:
                item_geometry = None
            item["prediction"] = predict_growth(
                species=species,
                growth_stage=growth_stage,
                clearance_m=item_clearance,
                features={
                    **payload,
                    **measurements,
                    "tree_stage": payload.get("tree_stage") or growth_stage,
                },
                geometry_status=measured.get("measurement_status") if measured else None,
                risk_status=measured.get("risk_status") if measured else None,
                geometry=item_geometry,
            )

    detected_tree = max(
        (item for item in detections if item.get("class_name") in TREE_CLASSES),
        key=lambda item: float(item.get("confidence") or 0),
        default=None,
    )
    species = str(detected_tree["class_name"]) if detected_tree else None
    prediction = (
        detected_tree["prediction"]
        if detected_tree
        else predict_growth(species=species, growth_stage=growth_stage, clearance_m=clearance_m)
    )
    calibrated_clearance = as_float((geometry.get("measurements") or {}).get("clearance_m"))
    if calibrated_clearance is not None:
        clearance_m = calibrated_clearance
        measurement_source = "calibrated_segmentation"
    if measurement_error and prediction.get("prediction_status") == "insufficient_input":
        prediction = {**prediction, "error": measurement_error}
    if render:
        try:
            annotated = render_result(frame, detections=detections)
            renderer = {"status": "rendered", "error": None}
        except Exception as exc:
            _LOGGER.warning("Renderer failed: %s", type(exc).__name__)
            annotated = frame.copy()
            renderer = {"status": "fallback_original", "error": "rendering unavailable"}
    else:
        annotated = frame
        renderer = {"status": "skipped", "error": None}

    limitations = ["Hasil otomatis harus diverifikasi sebelum digunakan untuk keputusan pemangkasan."]
    if detection.get("mode") == "baseline":
        limitations.insert(0, "Baseline COCO hanya membuktikan jalur inference, bukan deteksi species produksi.")
    detector = {
        "mode": detection.get("mode"),
        "model": detection.get("model"),
        "ready": detection.get("ready", False),
        "status": detection.get("status"),
        "error": detection.get("error"),
    }
    return {
        "status": "ready",
        "species": species,
        "growth_stage": growth_stage,
        "detector_status": detection.get("status"),
        "detector_role": detection.get("model_role"),
        "detector_error": detection.get("error"),
        "production_detector_ready": detection.get("production_ready", False),
        "tracking_status": detection.get("tracking_status"),
        "tracking_error": detection.get("tracking_error"),
        "detection_count": len(detections),
        "class_counts": detection.get("class_counts") or {},
        "detections": detections,
        "geometry": geometry,
        "clearance_m": clearance_m,
        "measurement_source": measurement_source,
        "prediction": prediction,
        "manual_review_required": not detection.get("production_ready") or prediction.get("prediction_status") != "ok",
        "limitations": limitations,
        "lighting": lighting,
        "detector": detector,
        "renderer": renderer,
    }, annotated


def process_capture(session_id: str, image_file: FileStorage | None, payload: dict[str, Any]) -> dict[str, Any]:
    existing = read_json(session_file(session_id, "result.json"), None)
    if isinstance(existing, dict) and existing.get("status") == "ready":
        return {**existing, "duplicate_ignored": True}
    metadata = load_metadata(session_id)
    if not metadata:
        raise FileNotFoundError("session not found")
    frame = decode_image(image_file)

    frame_payload = dict(metadata)
    for name in (
        "species",
        "growth_stage",
        "tree_stage",
        "clearance_m",
        "measurement_source",
        "lighting_mode",
        "capture_distance_m",
        "monitor_threshold_m",
        "action_threshold_m",
        "support_family",
        "support_spec",
        "support_buried_length_m",
        "support_standard_installation_confirmed",
        "support_full_height_confirmed",
        "tree_base_visible_confirmed",
    ):
        if payload.get(name) is not None and payload.get(name) != "":
            frame_payload[name] = payload[name]
    clearance_m, measurement_source = measurement_values(frame_payload)
    metadata = update_metadata(
        session_id,
        status="processing",
        capture_source=str(payload.get("capture_source") or "camera"),
        species=frame_payload.get("species") or None,
        growth_stage=frame_payload.get("tree_stage") or frame_payload.get("growth_stage") or None,
        location_name=str(frame_payload.get("location_name") or "").strip(),
        clearance_m=clearance_m,
        measurement_source=measurement_source,
    )

    original_path = session_file(session_id, "original.jpg")
    _write_image(original_path, frame)
    frame_result, annotated = process_frame(frame, frame_payload)
    detector = frame_result["detector"]
    renderer = frame_result.pop("renderer")
    detections = frame_result["detections"]
    prediction = frame_result["prediction"]
    detection = {
        "detector": detector,
        "tracking_status": frame_result["tracking_status"],
        "tracking_error": frame_result["tracking_error"],
        "detection_count": frame_result["detection_count"],
        "class_counts": frame_result["class_counts"],
        "detections": detections,
    }
    write_json(session_file(session_id, "detections.json"), detection)
    write_json(session_file(session_id, "growth.json"), prediction)

    species = frame_result.get("species")
    if species and species != metadata.get("species"):
        metadata = update_metadata(session_id, species=species)
    annotated_path = session_file(session_id, "annotated.jpg")
    _write_image(annotated_path, annotated)
    result = {
        **frame_result,
        "session_id": session_id,
        "created_at": now_iso(),
        "location_name": metadata.get("location_name") or None,
        "image_urls": {
            "annotated": f"/vegetation/session/{session_id}/annotated.jpg",
            "result": f"/vegetation/result/{session_id}",
        },
        "active": True,
    }
    developer = {
        "detection": detection,
        "geometry": frame_result["geometry"],
        "growth": prediction,
        "renderer": renderer,
        "files": {
            name: relative_path(session_file(session_id, name))
            for name in ("original.jpg", "annotated.jpg", "metadata.json", "result.json")
        },
    }
    write_json(session_file(session_id, "developer.json"), developer)
    classes = sorted({str(item.get("class_name")) for item in detections if item.get("class_name")})
    append_record(
        {
            "timestamp": result["created_at"],
            "session_id": session_id,
            "location_name": result["location_name"],
            "detector_status": result["detector_status"],
            "detected_classes": classes,
            "clearance_m": result["clearance_m"],
            "growth_status": prediction.get("prediction_status"),
            "prediction_window": prediction.get("prediction_window"),
            "result_path": relative_path(session_file(session_id, "result.json")),
            "annotated_path": relative_path(annotated_path),
        }
    )
    write_json(session_file(session_id, "result.json"), result)
    update_metadata(session_id, status="ready", processed=True)
    return result


def decode_image(image_file: FileStorage | None) -> np.ndarray:
    if image_file is None or not image_file.filename:
        raise ValueError("image is required")
    if image_file.mimetype not in SUPPORTED_IMAGE_TYPES:
        raise ValueError("unsupported image type")
    image_file.stream.seek(0)
    encoded = image_file.stream.read()
    if not encoded.startswith((JPEG_SIGNATURE, PNG_SIGNATURE)):
        raise ValueError("unsupported image format")
    image = cv2.imdecode(np.frombuffer(encoded, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("image cannot be decoded")
    height, width = image.shape[:2]
    if width < 64 or height < 64:
        raise ValueError("image resolution is too small")
    if width * height > 40_000_000:
        raise ValueError("image resolution is too large")
    return image


def measurement_values(payload: dict[str, Any]) -> tuple[float | None, str | None]:
    submitted = payload.get("clearance_m")
    clearance_m = as_float(submitted)
    if submitted is not None and submitted != "" and clearance_m is None:
        raise ValueError("clearance_m must be numeric")
    measurement_source = str(payload.get("measurement_source") or "").strip() or None
    if (clearance_m is None and measurement_source) or (
        clearance_m is not None and (not 0 <= clearance_m <= 100 or not measurement_source)
    ):
        raise ValueError("clearance_m in range 0-100 and measurement_source are required together")
    return clearance_m, measurement_source


def _adaptive_lighting(
    frame: np.ndarray,
    mode: str,
    tracking_session: str | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    sample = cv2.resize(frame, (160, 90), interpolation=cv2.INTER_AREA)
    luminance = cv2.cvtColor(sample, cv2.COLOR_BGR2YCrCb)[:, :, 0]
    with _LIGHTING_LOCK:
        if tracking_session and _LIGHTING_STATE["session"] != tracking_session:
            _LIGHTING_STATE.update(
                session=tracking_session,
                gamma=None,
                preview_brightness=None,
                correction_strength=None,
                clahe_strength=None,
                detections=[],
            )
        previous_detections = list(_LIGHTING_STATE["detections"]) if tracking_session else []
        previous_gamma = _LIGHTING_STATE["gamma"] if tracking_session else None
        previous_preview = _LIGHTING_STATE["preview_brightness"] if tracking_session else None
        previous_strength = _LIGHTING_STATE["correction_strength"] if tracking_session else None
        previous_clahe = _LIGHTING_STATE["clahe_strength"] if tracking_session else None

    foreground = _foreground_roi(luminance, previous_detections)
    foreground_mean = float(foreground.mean())
    global_mean = float(luminance.mean())
    p10, p50, p90 = (float(value) for value in np.percentile(luminance, (10, 50, 90)))
    shadow_ratio = float(np.mean(luminance < 48))
    highlight_ratio = float(np.mean(luminance > 220))
    local_contrast = float(foreground.std())
    automatic_scene = "normal"
    if (
        foreground_mean < 145
        and p90 - foreground_mean >= 50
        and (highlight_ratio >= 0.06 or p90 >= 225)
    ):
        automatic_scene = "backlight"
    elif foreground_mean < 120 and global_mean < 105 and highlight_ratio < 0.04 and p90 < 170:
        automatic_scene = "low_light"
    scene = automatic_scene if mode == "auto" else mode

    if mode == "normal":
        target = None
        measured_strength = 0.0
        measured_gamma = 1.0
        measured_clahe = 0.0
    else:
        target = {"normal": 155.0, "backlight": 165.0, "low_light": 170.0}[scene]
        foreground_deficit = float(np.clip((target - foreground_mean) / target, 0.0, 1.0))
        global_deficit = float(np.clip((target - global_mean) / target, 0.0, 1.0))
        weighted_deficit = 0.8 * foreground_deficit + 0.2 * min(foreground_deficit, global_deficit)
        measured_strength = 1.0 - (1.0 - weighted_deficit) ** 2.5
        level = float(np.clip(foreground_mean, 1.0, 254.0)) / 255.0
        raw_gamma = float(np.clip(np.log(target / 255.0) / np.log(level), 0.35, 1.60))
        measured_gamma = 1.0 + (raw_gamma - 1.0) * measured_strength
        measured_clahe = measured_strength if foreground_mean < target and local_contrast < 38 else 0.0
    measured_preview = 1.0 + 0.65 * measured_strength
    alpha = 0.35
    if mode == "normal" or measured_strength == 0.0:
        gamma, preview_brightness, correction_strength, clahe_strength = 1.0, 1.0, 0.0, 0.0
    else:
        gamma = measured_gamma if previous_gamma is None else previous_gamma * (1 - alpha) + measured_gamma * alpha
        preview_brightness = (
            measured_preview if previous_preview is None else previous_preview * (1 - alpha) + measured_preview * alpha
        )
        correction_strength = (
            measured_strength if previous_strength is None else previous_strength * (1 - alpha) + measured_strength * alpha
        )
        clahe_strength = (
            measured_clahe if previous_clahe is None else previous_clahe * (1 - alpha) + measured_clahe * alpha
        )
    if tracking_session:
        with _LIGHTING_LOCK:
            if _LIGHTING_STATE["session"] == tracking_session:
                _LIGHTING_STATE.update(
                    gamma=gamma,
                    preview_brightness=preview_brightness,
                    correction_strength=correction_strength,
                    clahe_strength=clahe_strength,
                )

    enhanced = frame
    clip_limit = 0.0
    if abs(gamma - 1.0) >= 0.01 or clahe_strength >= 0.02:
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        source_luminance = ycrcb[:, :, 0]
        levels = np.arange(256, dtype=np.float32)
        gamma_curve = 255.0 * ((levels / 255.0) ** gamma)
        highlight_protection = np.interp(levels, (0, 170, 210, 220, 255), (1, 1, 0.25, 0, 0))
        corrected = levels + (gamma_curve - levels) * highlight_protection
        shadow_profile = np.interp(levels, (0, 80, 150, 210, 255), (1, 1, 0.45, 0, 0))
        maximum_lift = {"normal": 45.0, "backlight": 65.0, "low_light": 60.0}[scene]
        lift = maximum_lift * correction_strength * shadow_profile
        corrected += lift * (1.0 - corrected / 255.0)
        adjusted = cv2.LUT(source_luminance, np.clip(corrected, 0, 255).astype(np.uint8))
        if clahe_strength >= 0.02:
            clip_limit = {"auto": 2.3, "backlight": 2.5, "low_light": 2.4}[mode]
            contrasted = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8)).apply(adjusted)
            adjusted = cv2.addWeighted(adjusted, 1.0 - 0.55 * clahe_strength, contrasted, 0.55 * clahe_strength, 0)
        ycrcb[:, :, 0] = adjusted
        enhanced = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

    if mode == "normal":
        exposure_ratio = 0.0
    else:
        exposure_ratio = {"normal": 0.35, "backlight": 0.70, "low_light": 0.50}[scene] * correction_strength
    return enhanced, {
        "mode": mode,
        "scene": scene,
        "foreground_mean": round(foreground_mean, 2),
        "global_mean": round(global_mean, 2),
        "p10": round(p10, 2),
        "p50": round(p50, 2),
        "p90": round(p90, 2),
        "shadow_ratio": round(shadow_ratio, 4),
        "highlight_ratio": round(highlight_ratio, 4),
        "local_contrast": round(local_contrast, 2),
        "target_luminance": target,
        "correction_strength": round(correction_strength, 4),
        "gamma": round(gamma, 4),
        "clahe_strength": round(clahe_strength, 4),
        "clahe_clip_limit": clip_limit,
        "preview_brightness": round(preview_brightness, 4),
        "preview_contrast": round(1.0 + 0.2 * correction_strength, 4),
        "exposure_ratio": round(exposure_ratio, 4),
    }


def _foreground_roi(luminance: np.ndarray, detections: list[dict[str, Any]]) -> np.ndarray:
    height, width = luminance.shape
    dominant = None
    dominant_score = 0.0
    for detection in detections:
        box = detection.get("bbox_xywhn")
        try:
            center_x, center_y, box_width, box_height = (float(value) for value in box)
            confidence = float(detection.get("confidence") or 0)
        except (TypeError, ValueError):
            continue
        if not all(np.isfinite((center_x, center_y, box_width, box_height, confidence))):
            continue
        area = box_width * box_height
        if confidence <= 0 or box_width <= 0 or box_height <= 0 or area < 0.01:
            continue
        score = area * confidence * (1.1 if detection.get("track_id") is not None else 1.0)
        if score > dominant_score:
            dominant = (center_x, center_y, box_width * 0.85, box_height * 0.85)
            dominant_score = score
    if dominant:
        center_x, center_y, box_width, box_height = dominant
        x1 = max(0, min(width - 1, round((center_x - box_width / 2) * width)))
        x2 = max(x1 + 1, min(width, round((center_x + box_width / 2) * width)))
        y1 = max(0, min(height - 1, round((center_y - box_height / 2) * height)))
        y2 = max(y1 + 1, min(height, round((center_y + box_height / 2) * height)))
        return luminance[y1:y2, x1:x2]
    return luminance[height // 5 : height * 4 // 5, width // 4 : width * 3 // 4]


def _write_image(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_JPEG_QUALITY, 92]):
        raise OSError("image cannot be written")
