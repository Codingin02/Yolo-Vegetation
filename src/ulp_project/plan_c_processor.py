"""Snapshot processing orchestration for Plan C."""

from __future__ import annotations

import base64
from datetime import datetime
import json
import math
from pathlib import Path
import re
from typing import Any

from .plan_c_ai_core_consensus import run_ai_consensus, validate_ai_bbox
from .plan_c_free_vision_config import load_free_vision_config, redact_config
from .plan_c_free_vision_schema import normalize_detection_payload
from .plan_c_geometry import DEFAULT_GEOMETRY_PARAMETERS, compute_plan_c_geometry
from .plan_c_growth_model import build_growth_summary, load_growth_profile
from .plan_c_quality_layer import apply_plan_c_quality_layer
from .plan_c_session import load_plan_c_metadata, save_plan_c_metadata, update_plan_c_status
from .plan_c_storage import (
    append_marker,
    append_plan_c_record,
    ensure_session_dir,
    relative_to_project,
    session_file,
    to_float,
    utc_now_iso,
    write_json,
)
from .plan_c_yolo import run_yolo_post_capture
from .plan_c_yolo_compatible_renderer import render_yolo_compatible_annotation

_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{8,128}$")


def process_plan_c_snapshot(session_id: str, *, image_file: Any | None, payload: dict[str, Any]) -> dict[str, Any]:
    metadata = load_plan_c_metadata(session_id)
    idempotency_key = _normalize_idempotency_key(payload.get("idempotency_key"))
    duplicate = _duplicate_response_if_processed(session_id, metadata, idempotency_key)
    if duplicate:
        return duplicate
    if idempotency_key:
        metadata = _mark_idempotency_processing(session_id, metadata, idempotency_key)

    folder = ensure_session_dir(session_id)
    original_path = folder / "original.jpg"
    annotated_path = folder / "annotated.jpg"
    _save_snapshot_image(original_path, image_file=image_file, payload=payload)

    metadata.update(_build_snapshot_metadata(session_id, payload, original_path, idempotency_key=idempotency_key))
    metadata["status"] = "PLAN_C_PROCESSING"
    metadata["snapshot_status"] = "PLAN_C_SNAPSHOT_ACCEPTED"
    metadata["processing_status"] = "PLAN_C_PROCESSING"
    save_plan_c_metadata(session_id, metadata)

    yolo_raw = run_yolo_post_capture(original_path, annotated_path)
    write_json(session_file(session_id, "yolo_raw.json"), yolo_raw)

    image_width, image_height = _read_image_size(original_path)
    free_vision_config = load_free_vision_config()
    detection_result = _detect_snapshot(
        original_path=original_path,
        payload=payload,
        image_width=image_width,
        image_height=image_height,
        free_vision_config=free_vision_config,
        yolo_raw=yolo_raw,
    )
    detection_result = apply_plan_c_quality_layer(detection_result, image_width=image_width, image_height=image_height)
    detection_result = _restore_single_class_runtime_detection(detection_result, yolo_raw=yolo_raw)

    capture_month = _capture_month(metadata.get("snapshot_captured_at"))
    preliminary_growth = build_growth_summary(
        clearance_m=None,
        threshold_m=DEFAULT_GEOMETRY_PARAMETERS["vegetation_clearance_threshold_m"],
        month=capture_month,
    )
    ai_raw = run_ai_consensus(
        original_path,
        detection_result.get("detections", []),
        preliminary_growth,
        metadata,
    )
    detection_result = _apply_ai_consensus_tree_bbox(
        detection_result,
        ai_raw=ai_raw,
        image_width=image_width,
        image_height=image_height,
    )
    write_json(session_file(session_id, "ai_raw.json"), ai_raw)

    geometry = compute_plan_c_geometry(
        detection_result.get("detections", []),
        metadata=metadata,
        manual_inputs=metadata.get("manual_inputs", {}),
    )
    write_json(session_file(session_id, "geometry.json"), geometry)

    growth = build_growth_summary(
        clearance_m=geometry.get("clearance_estimate_m"),
        threshold_m=DEFAULT_GEOMETRY_PARAMETERS["vegetation_clearance_threshold_m"],
        month=capture_month,
    )
    growth = _adjust_growth_for_species(growth, detection_result)
    prediction = _build_days_prediction(geometry=geometry, growth=growth)
    growth.update(prediction)
    risk_status = prediction.get("risk_status") or geometry.get("risk_status") or "DATA_TIDAK_CUKUP"
    prediction_window = prediction.get("prediction_window") or growth.get("prediction_window") or "data tidak cukup"
    geometry = {
        **geometry,
        "gps_distance_from_anchor_m": (metadata.get("gps") or {}).get("gps_distance_from_anchor_m"),
        "estimated_steps_from_anchor": (metadata.get("gps") or {}).get("estimated_steps_from_anchor"),
    }
    zone_decision = _finalize_system_c_zone_decision(
        detections=detection_result.get("detections", []),
        geometry=geometry,
        growth=growth,
        ai_raw=ai_raw,
        metadata=metadata,
        image_width=image_width,
        image_height=image_height,
    )
    risk_status = zone_decision["risk_status"]
    prediction_window = zone_decision["prediction_window"]
    geometry.update(zone_decision["geometry_updates"])
    growth.update(zone_decision["growth_updates"])
    detection_result.update(zone_decision["detection_updates"])
    write_json(session_file(session_id, "geometry.json"), geometry)

    render_status = render_yolo_compatible_annotation(
        original_path,
        annotated_path,
        detection_result.get("detections", []),
        geometry=geometry,
        growth=growth,
        risk_status=risk_status,
        prediction_window=prediction_window,
        zone_bands=zone_decision["zone_bands"],
        final_detection_source=detection_result.get("final_detection_source", "NONE"),
        zone_method=zone_decision["zone_method"],
        zone_final=zone_decision["zone_final"],
    )

    result = _build_result_payload(
        session_id=session_id,
        metadata=metadata,
        original_path=original_path,
        annotated_path=annotated_path,
        yolo_raw=yolo_raw,
        ai_raw=ai_raw,
        detection_result=detection_result,
        render_status=render_status,
        geometry=geometry,
        growth=growth,
        risk_status=risk_status,
        prediction_window=prediction_window,
        idempotency_key=idempotency_key,
    )
    write_json(session_file(session_id, "result.json"), result)

    record = _build_record(result)
    append_status = append_plan_c_record(record)
    marker_status = append_marker(_build_marker(result))

    if idempotency_key:
        metadata = _mark_idempotency_completed(
            session_id,
            metadata,
            idempotency_key,
            result=result,
            append_status=append_status,
            marker_status=marker_status,
        )

    developer = _build_developer_payload(
        session_id=session_id,
        metadata=metadata,
        yolo_raw=yolo_raw,
        ai_raw=ai_raw,
        detection_result=detection_result,
        render_status=render_status,
        free_vision_config=free_vision_config,
        geometry=geometry,
        growth=growth,
        append_status=append_status,
        marker_status=marker_status,
    )
    write_json(session_file(session_id, "developer.json"), developer)

    update_plan_c_status(
        session_id,
        status="PLAN_C_RESULT_READY",
        processing_status="PLAN_C_RESULT_READY",
        result_status="PLAN_C_RESULT_READY",
        last_result_path=str(session_file(session_id, "result.json")),
    )

    return {
        "ok": True,
        "status": "PLAN_C_RESULT_READY",
        "accepted_status": "PLAN_C_SNAPSHOT_ACCEPTED",
        "session_id": session_id,
        "idempotency_key": idempotency_key,
        "duplicate_ignored": False,
        "result_url": f"/plan-c/result/{session_id}",
        "processing_url": f"/plan-c/processing/{session_id}",
        "developer_url": f"/plan-c/developer/{session_id}",
        "risk_status": result["risk_status"],
        "prediction_window": result["prediction_window"],
        "detection_status": result.get("detection_status"),
        "detection_count": result.get("detection_count"),
        "append_status": append_status,
        "marker_status": marker_status,
    }


def _normalize_idempotency_key(value: Any) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    if not _IDEMPOTENCY_PATTERN.match(cleaned):
        raise ValueError("PLAN_C_IDEMPOTENCY_KEY_INVALID")
    return cleaned


def _duplicate_response_if_processed(session_id: str, metadata: dict[str, Any], idempotency_key: str) -> dict[str, Any] | None:
    if not idempotency_key:
        return None
    item = _idempotency_items(metadata).get(idempotency_key)
    if not isinstance(item, dict):
        return None
    result = _load_existing_result(session_id)
    if item.get("status") == "completed" and result:
        return {
            "ok": True,
            "status": "PLAN_C_SNAPSHOT_ALREADY_PROCESSED",
            "duplicate_status": "DUPLICATE_IGNORED",
            "duplicate_ignored": True,
            "session_id": session_id,
            "idempotency_key": idempotency_key,
            "http_status": 200,
            "result_url": f"/plan-c/result/{session_id}",
            "processing_url": f"/plan-c/processing/{session_id}",
            "developer_url": f"/plan-c/developer/{session_id}",
            "risk_status": result.get("risk_status"),
            "prediction_window": result.get("prediction_window"),
            "append_status": {"status": "DUPLICATE_IGNORED", "record_appended": False},
            "marker_status": {"status": "DUPLICATE_IGNORED", "marker_appended": False},
        }
    if item.get("status") == "processing":
        return {
            "ok": True,
            "status": "PLAN_C_SNAPSHOT_PROCESSING",
            "duplicate_status": "DUPLICATE_IGNORED",
            "duplicate_ignored": True,
            "session_id": session_id,
            "idempotency_key": idempotency_key,
            "http_status": 202,
            "result_url": f"/plan-c/result/{session_id}",
            "processing_url": f"/plan-c/processing/{session_id}",
        }
    return None


def _mark_idempotency_processing(session_id: str, metadata: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
    items = _idempotency_items(metadata)
    items[idempotency_key] = {
        "status": "processing",
        "received_at": utc_now_iso(),
        "completed_at": "",
        "result_path": "",
    }
    metadata["idempotency_keys"] = items
    metadata["last_idempotency_key"] = idempotency_key
    save_plan_c_metadata(session_id, metadata)
    return metadata


def _mark_idempotency_completed(
    session_id: str,
    metadata: dict[str, Any],
    idempotency_key: str,
    *,
    result: dict[str, Any],
    append_status: dict[str, Any],
    marker_status: dict[str, Any],
) -> dict[str, Any]:
    items = _idempotency_items(metadata)
    current = dict(items.get(idempotency_key) or {})
    current.update(
        {
            "status": "completed",
            "completed_at": utc_now_iso(),
            "result_path": result.get("files", {}).get("result", ""),
            "risk_status": result.get("risk_status"),
            "prediction_window": result.get("prediction_window"),
            "csv_rows_after": append_status.get("csv_rows_after"),
            "jsonl_rows_after": append_status.get("jsonl_rows_after"),
            "marker_count_after": marker_status.get("marker_count_after"),
        }
    )
    items[idempotency_key] = current
    metadata["idempotency_keys"] = items
    metadata["last_idempotency_key"] = idempotency_key
    save_plan_c_metadata(session_id, metadata)
    return metadata


def _idempotency_items(metadata: dict[str, Any]) -> dict[str, Any]:
    items = metadata.get("idempotency_keys")
    return items if isinstance(items, dict) else {}


def _load_existing_result(session_id: str) -> dict[str, Any]:
    try:
        from .plan_c_storage import read_json

        result = read_json(session_file(session_id, "result.json"), default={}) or {}
    except Exception:
        return {}
    return result if isinstance(result, dict) else {}


def _save_snapshot_image(original_path: Path, *, image_file: Any | None, payload: dict[str, Any]) -> None:
    original_path.parent.mkdir(parents=True, exist_ok=True)
    if image_file is not None:
        image_file.save(original_path)
        return
    image_data = str(payload.get("image_data") or "").strip()
    if image_data.startswith("data:image"):
        image_data = image_data.split(",", 1)[1]
    if image_data:
        original_path.write_bytes(base64.b64decode(image_data))
        return
    raise ValueError("PLAN_C_SNAPSHOT_IMAGE_REQUIRED")


def _build_snapshot_metadata(session_id: str, payload: dict[str, Any], original_path: Path, *, idempotency_key: str = "") -> dict[str, Any]:
    gps = _extract_gps(payload)
    manual_inputs = {
        "manual_distance_m": to_float(payload.get("manual_distance_m")),
        "manual_tree_height_m": to_float(payload.get("manual_tree_height_m")),
        "manual_clearance_m": to_float(payload.get("manual_clearance_m")),
        "manual_conductor_height_m": to_float(payload.get("manual_conductor_height_m")),
        "manual_structure_height_m": to_float(payload.get("manual_structure_height_m") or payload.get("structure_height_m")),
        "ground_reference_y": to_float(payload.get("ground_reference_y")),
        "conductor_y": to_float(payload.get("conductor_y")),
        "manual_zone": str(payload.get("manual_zone") or payload.get("zone") or "").strip(),
    }
    return {
        "session_id": session_id,
        "point_id": str(payload.get("point_id") or "pohon_sono").strip() or "pohon_sono",
        "idempotency_key": idempotency_key,
        "snapshot_captured_at": utc_now_iso(),
        "capture_source": str(payload.get("capture_source") or "camera").strip() or "camera",
        "operator_note": str(payload.get("operator_note") or payload.get("notes") or "").strip(),
        "gps": gps,
        "gps_status": "GPS_VALID" if gps.get("gps_valid") else "NO_GPS_NO_MARKER",
        "manual_inputs": manual_inputs,
        "original_path": str(original_path),
    }


def _extract_gps(payload: dict[str, Any]) -> dict[str, Any]:
    tree_anchor = _json_payload_field(payload.get("tree_anchor_gps"))
    shutter = _json_payload_field(payload.get("shutter_gps"))
    track_summary = _json_payload_field(payload.get("gps_track_summary"))
    track_points = _json_payload_field(payload.get("gps_track_points"))
    latitude = to_float(_dict_get(shutter, "latitude") or payload.get("latitude") or payload.get("lat"))
    longitude = to_float(_dict_get(shutter, "longitude") or payload.get("longitude") or payload.get("lon") or payload.get("lng"))
    accuracy = to_float(_dict_get(shutter, "accuracy_m") or payload.get("gps_accuracy_m") or payload.get("accuracy"))
    gps_valid = latitude is not None and longitude is not None
    raw_status = str(payload.get("gps_status") or "").strip()
    gps_status = raw_status if raw_status else "GPS_NOT_READY"
    gps_quality_status = "GPS_NOT_READY"
    distance_m = to_float(payload.get("gps_distance_from_anchor_m") or _dict_get(track_summary, "gps_distance_from_anchor_m"))
    if distance_m is None:
        distance_m = _haversine_m(tree_anchor, {"latitude": latitude, "longitude": longitude} if gps_valid else shutter)
    estimated_steps = to_float(payload.get("estimated_steps_from_anchor") or _dict_get(track_summary, "estimated_steps_from_anchor"))
    if estimated_steps is None and distance_m is not None:
        estimated_steps = round(distance_m / 0.75, 1)
    distance_status = str(payload.get("gps_distance_status") or _dict_get(track_summary, "gps_distance_status") or "").strip()
    if gps_valid:
        gps_status = "GPS_READY"
        gps_quality_status = "GPS_LOW_ACCURACY_EVIDENCE_ONLY" if accuracy is not None and accuracy > 20 else "GPS_ACCURACY_ACCEPTED"
        if not distance_status:
            distance_status = "GPS_DISTANCE_LOW_CONFIDENCE" if accuracy is not None and accuracy > 10 else "GPS_DISTANCE_ACCEPTED"
    return {
        "latitude": latitude,
        "longitude": longitude,
        "gps_accuracy_m": accuracy,
        "gps_valid": gps_valid,
        "gps_status": gps_status,
        "gps_quality_status": gps_quality_status,
        "gps_distance_status": distance_status or "GPS_NOT_READY",
        "gps_distance_from_anchor_m": round(distance_m, 2) if distance_m is not None else None,
        "estimated_steps_from_anchor": round(estimated_steps, 1) if estimated_steps is not None else None,
        "estimated_steps_note": "Estimasi langkah berbasis jarak GPS / 0.75 m, bukan sensor langkah aktual.",
        "tree_anchor_gps": tree_anchor,
        "shutter_gps": shutter,
        "gps_track_summary": track_summary,
        "gps_track_points": track_points if isinstance(track_points, list) else [],
        "gps_source": str(payload.get("gps_source") or _dict_get(shutter, "gps_source") or ("GPS_SOURCE_BROWSER" if gps_valid else "GPS_SOURCE_UNAVAILABLE")),
    }


def _build_result_payload(
    *,
    session_id: str,
    metadata: dict[str, Any],
    original_path: Path,
    annotated_path: Path,
    yolo_raw: dict[str, Any],
    ai_raw: dict[str, Any],
    detection_result: dict[str, Any],
    render_status: dict[str, Any],
    geometry: dict[str, Any],
    growth: dict[str, Any],
    risk_status: str,
    prediction_window: str,
    idempotency_key: str = "",
) -> dict[str, Any]:
    gps = metadata.get("gps", {})
    detection_count = int(detection_result.get("detection_count") or len(detection_result.get("detections") or []))
    detection_status = str(detection_result.get("status") or detection_result.get("pipeline_status") or "DATA_TIDAK_CUKUP")
    return {
        "status": "PLAN_C_RESULT_READY",
        "runtime_mode": "PLAN_C_SYSTEM_C_SINGLE_CLASS_POHON_SONO",
        "detector": "YOLOv8",
        "yolo_mode": "single_class",
        "ai_core_mode": ai_raw.get("ai_core_mode", "THREE_PROVIDER_CONSENSUS"),
        "ai_providers_enabled": ai_raw.get("providers_enabled", []),
        "ai_provider_statuses": ai_raw.get("provider_statuses", []),
        "final_detection_source": detection_result.get("final_detection_source", "NONE"),
        "detected_primary_object": "pohon_sono",
        "multi_class_runtime": False,
        "conductor_required_for_detection": False,
        "session_id": session_id,
        "point_id": metadata.get("point_id") or "pohon_sono",
        "idempotency_key": idempotency_key,
        "created_at": utc_now_iso(),
        "risk_status": risk_status,
        "prediction_window": prediction_window,
        "tree_height_estimate_m": geometry.get("tree_height_estimate_m"),
        "clearance_estimate_m": geometry.get("clearance_estimate_m"),
        "conductor_height_m": geometry.get("conductor_height_m"),
        "structure_height_m": geometry.get("structure_height_m"),
        "structure_height_source": geometry.get("structure_height_source"),
        "prediction_days": growth.get("prediction_days"),
        "prediction_months": growth.get("prediction_months"),
        "prediction_remaining_days": growth.get("prediction_remaining_days"),
        "prediction_months_days": growth.get("prediction_months_days"),
        "remaining_clearance_to_tebang_m": growth.get("remaining_clearance_to_tebang_m"),
        "growth_rate_m_per_day": growth.get("growth_rate_m_per_day"),
        "manual_review_required": bool(
            geometry.get("manual_review_required")
            or detection_result.get("manual_review_required")
            or risk_status == "DATA_TIDAK_CUKUP"
        ),
        "detection_status": detection_status,
        "detection_count": detection_count,
        "detections": _operator_detections(detection_result.get("detections", [])),
        "tree_species_status": detection_result.get("tree_species_status") or geometry.get("tree_species_status") or "unknown",
        "conductor_status": detection_result.get("conductor_status") or geometry.get("conductor_status") or "manual/reference only",
        "structure_status": detection_result.get("structure_status") or geometry.get("structure_status") or "manual/reference only",
        "zone_status": render_status.get("zone_summary", {}).get("zone_status") or detection_result.get("zone_status") or "unavailable",
        "zone_precision": render_status.get("zone_summary", {}).get("zone_precision") or geometry.get("zone_precision") or "unavailable",
        "zone_overlay_status": render_status.get("zone_overlay_status") or geometry.get("zone_overlay_status"),
        "zone_method": geometry.get("zone_method") or render_status.get("zone_summary", {}).get("zone_method"),
        "zone_final": geometry.get("zone_final") or render_status.get("zone_summary", {}).get("zone_final"),
        "zone_summary": render_status.get("zone_summary", {}),
        "ground_reference_y": geometry.get("ground_reference_y"),
        "ground_reference_status": render_status.get("zone_summary", {}).get("ground_reference_status") or geometry.get("ground_reference_status"),
        "conductor_y": geometry.get("conductor_y"),
        "meter_per_pixel": geometry.get("meter_per_pixel") or geometry.get("meter_per_px"),
        "meter_per_pixel_source": geometry.get("meter_per_pixel_source"),
        "zone_tebang_y1": render_status.get("zone_summary", {}).get("zone_tebang_y1") or geometry.get("zone_tebang_y1"),
        "zone_tebang_y2": render_status.get("zone_summary", {}).get("zone_tebang_y2") or geometry.get("zone_tebang_y2"),
        "zone_pantau_y1": render_status.get("zone_summary", {}).get("zone_pantau_y1") or geometry.get("zone_pantau_y1"),
        "zone_pantau_y2": render_status.get("zone_summary", {}).get("zone_pantau_y2") or geometry.get("zone_pantau_y2"),
        "zone_aman_y1": render_status.get("zone_summary", {}).get("zone_aman_y1") or geometry.get("zone_aman_y1"),
        "zone_aman_y2": render_status.get("zone_summary", {}).get("zone_aman_y2") or geometry.get("zone_aman_y2"),
        "conductor_group_count": detection_result.get("conductor_group_count") or geometry.get("conductor_group_count") or 0,
        "conductor_lines": detection_result.get("conductor_lines") or geometry.get("conductor_lines") or [],
        "operator_detection_label": detection_result.get("operator_detection_label", "Detection"),
        "operator_output_format": detection_result.get("operator_output_format", "YOLOv8 single-class"),
        "consensus_status": detection_result.get("consensus_status"),
        "review_status": "MANUAL_REVIEW_REQUIRED"
        if detection_result.get("manual_review_required") or risk_status == "DATA_TIDAK_CUKUP"
        else "REVIEW_OPTIONAL",
        "yolo_status": yolo_raw.get("status"),
        "yolo_summary": {
            "status": yolo_raw.get("status"),
            "detection_count": yolo_raw.get("detection_count", 0),
            "manual_review_required": yolo_raw.get("manual_review_required", True),
            "model_path": yolo_raw.get("model_path", ""),
            "model_policy": yolo_raw.get("model_policy", "single_class_pohon_sono"),
            "active_detection_target": yolo_raw.get("active_detection_target", "pohon_sono"),
            "multi_class_runtime": yolo_raw.get("multi_class_runtime", False),
        },
        "ai_consensus_summary": ai_raw.get("summary", {}),
        "detection_summary": {
            "status": detection_status,
            "detection_count": detection_count,
            "detection_target": "pohon_sono",
            "final_detection_source": detection_result.get("final_detection_source", "NONE"),
            "operator_output_format": detection_result.get("operator_output_format", "YOLOv8 single-class"),
            "manual_review_required": detection_result.get("manual_review_required", True),
            "render_status": render_status.get("status"),
            "tree_species_status": detection_result.get("tree_species_status") or geometry.get("tree_species_status") or "unknown",
            "conductor_status": detection_result.get("conductor_status") or geometry.get("conductor_status") or "manual/reference only",
            "ground_reference_status": render_status.get("zone_summary", {}).get("ground_reference_status") or geometry.get("ground_reference_status"),
            "zone_status": render_status.get("zone_summary", {}).get("zone_status") or geometry.get("zone_status") or "unavailable",
            "zone_precision": render_status.get("zone_summary", {}).get("zone_precision") or geometry.get("zone_precision") or "unavailable",
            "conductor_group_count": detection_result.get("conductor_group_count") or geometry.get("conductor_group_count") or 0,
            "multi_class_runtime": False,
            "conductor_required_for_detection": False,
        },
        "gps_summary": gps,
        "gps_status": gps.get("gps_quality_status") or gps.get("gps_status") or "GPS_NOT_READY",
        "gps_distance_status": gps.get("gps_distance_status"),
        "gps_distance_from_anchor_m": gps.get("gps_distance_from_anchor_m"),
        "estimated_steps_from_anchor": gps.get("estimated_steps_from_anchor"),
        "estimated_steps_note": gps.get("estimated_steps_note"),
        "geometry_status": geometry.get("geometry_status"),
        "growth_profile_status": growth.get("growth_profile_status"),
        "growth_rate_m_per_quarter": growth.get("growth_rate_m_per_quarter"),
        "data_source_type": growth.get("data_source_type"),
        "observed_or_proxy": growth.get("observed_or_proxy"),
        "confidence_level": growth.get("confidence_level"),
        "limitations": growth.get("limitations", []),
        "growth_source_summary": growth.get("source_summary", {}),
        "detection_image_width": detection_result.get("image_width"),
        "detection_image_height": detection_result.get("image_height"),
        "files": {
            "original": relative_to_project(original_path),
            "annotated": relative_to_project(annotated_path),
            "result": relative_to_project(session_file(session_id, "result.json")),
            "developer": relative_to_project(session_file(session_id, "developer.json")),
        },
        "image_urls": {"annotated": f"/plan-c/session/{session_id}/annotated.jpg"},
        "links": {
            "result": f"/plan-c/result/{session_id}",
            "map": "/plan-c/map",
            "developer": f"/plan-c/developer/{session_id}",
        },
        "not_final_pln_measurement": True,
    }


def _build_record(result: dict[str, Any]) -> dict[str, Any]:
    gps = result.get("gps_summary", {})
    files = result.get("files", {})
    return {
        "record_id": f"{result['session_id']}_{datetime.now().strftime('%H%M%S')}",
        "session_id": result["session_id"],
        "created_at": result["created_at"],
        "risk_status": result.get("risk_status"),
        "prediction_window": result.get("prediction_window"),
        "manual_review_required": result.get("manual_review_required"),
        "latitude": gps.get("latitude"),
        "longitude": gps.get("longitude"),
        "gps_accuracy_m": gps.get("gps_accuracy_m"),
        "yolo_status": result.get("detection_status") or result.get("yolo_status"),
        "ai_validator_status": "",
        "geometry_status": result.get("geometry_status"),
        "growth_profile_status": result.get("growth_profile_status"),
        "growth_rate_m_per_quarter": result.get("growth_rate_m_per_quarter"),
        "data_source_type": result.get("data_source_type"),
        "original_path": files.get("original"),
        "annotated_path": files.get("annotated"),
        "result_path": files.get("result"),
    }


def _build_marker(result: dict[str, Any]) -> dict[str, Any]:
    gps = result.get("gps_summary", {})
    return {
        "marker_id": result["session_id"],
        "session_id": result["session_id"],
        "created_at": result["created_at"],
        "latitude": gps.get("latitude"),
        "longitude": gps.get("longitude"),
        "gps_accuracy_m": gps.get("gps_accuracy_m"),
        "gps_status": result.get("gps_status"),
        "risk_status": result.get("risk_status"),
        "prediction_window": result.get("prediction_window"),
        "result_url": result.get("links", {}).get("result"),
        "developer_url": result.get("links", {}).get("developer"),
        "source": "plan_c_snapshot",
        "active_status": result.get("operator_feedback_status", "active"),
    }


def _build_developer_payload(
    *,
    session_id: str,
    metadata: dict[str, Any],
    yolo_raw: dict[str, Any],
    ai_raw: dict[str, Any],
    detection_result: dict[str, Any],
    render_status: dict[str, Any],
    free_vision_config: dict[str, Any],
    geometry: dict[str, Any],
    growth: dict[str, Any],
    append_status: dict[str, Any],
    marker_status: dict[str, Any],
) -> dict[str, Any]:
    growth_profile = load_growth_profile()
    return {
        "status": "PLAN_C_DEVELOPER_DIAGNOSTICS_READY",
        "session_id": session_id,
        "generated_at": utc_now_iso(),
        "raw_diagnostics": True,
        "metadata": metadata,
        "yolo_raw": yolo_raw,
        "ai_raw": ai_raw,
        "free_vision_detection": detection_result,
        "free_vision_config_redacted": redact_config(free_vision_config),
        "yolo_compatible_render": render_status,
        "geometry": geometry,
        "growth": growth,
        "growth_dataset_diagnostics": growth_profile,
        "append_status": append_status,
        "marker_status": marker_status,
        "file_paths": {name: str(session_file(session_id, name)) for name in [
            "original.jpg",
            "annotated.jpg",
            "result.json",
            "developer.json",
            "metadata.json",
            "yolo_raw.json",
            "ai_raw.json",
            "geometry.json",
        ]},
        "route_diagnostics": {
            "result": f"/plan-c/result/{session_id}",
            "developer": f"/plan-c/developer/{session_id}",
            "api_result": f"/api/plan-c/session/{session_id}/result",
            "api_status": f"/api/plan-c/session/{session_id}/status",
        },
        "warnings": [
            "Plan C bukan realtime dan bukan pengganti pengukuran manual PLN.",
            "Runtime operator memakai YOLOv8 single-class pohon_sono; geometri clearance tetap membutuhkan review lapangan.",
        ],
        "errors": [],
    }


def _capture_month(timestamp: Any) -> int | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).month
    except ValueError:
        return None


def _build_days_prediction(*, geometry: dict[str, Any], growth: dict[str, Any]) -> dict[str, Any]:
    clearance = to_float(geometry.get("clearance_estimate_m"))
    threshold = DEFAULT_GEOMETRY_PARAMETERS["vegetation_clearance_threshold_m"]
    rate_quarter = to_float(growth.get("growth_rate_m_per_quarter"))
    geometry_risk = str(geometry.get("risk_status") or "DATA_TIDAK_CUKUP")
    if geometry_risk.startswith("DATA_TIDAK_CUKUP") or clearance is None:
        return {
            "prediction_status": geometry_risk,
            "risk_status": geometry_risk,
            "prediction_window": "data tidak cukup",
            "prediction_days": None,
            "prediction_months": None,
            "prediction_remaining_days": None,
            "prediction_months_days": "data tidak cukup",
            "remaining_clearance_to_tebang_m": None,
            "growth_rate_m_per_day": None,
        }
    if rate_quarter is None or rate_quarter <= 0:
        return {
            "prediction_status": "DATA_TIDAK_CUKUP_GROWTH_PROFILE",
            "risk_status": "DATA_TIDAK_CUKUP_GROWTH_PROFILE",
            "prediction_window": "data tidak cukup",
            "prediction_days": None,
            "prediction_months": None,
            "prediction_remaining_days": None,
            "prediction_months_days": "data tidak cukup",
            "remaining_clearance_to_tebang_m": round(clearance - threshold, 3),
            "growth_rate_m_per_day": None,
        }

    growth_rate_per_day = rate_quarter / 91.25
    remaining = clearance - threshold
    if clearance <= threshold:
        days = 0
        risk_status = "ZONA_TEBANG"
    else:
        days = max(0, math.floor(remaining / growth_rate_per_day))
        risk_status = geometry_risk if geometry_risk in {"AMAN", "PANTAU", "ZONA_TEBANG"} else "PANTAU"
    months = days // 30
    remaining_days = days % 30
    window = f"{months} bulan {remaining_days} hari"
    return {
        "prediction_status": "PREDICTION_DAYS_READY",
        "risk_status": risk_status,
        "prediction_window": window,
        "prediction_days": days,
        "prediction_months": months,
        "prediction_remaining_days": remaining_days,
        "prediction_months_days": window,
        "remaining_clearance_to_tebang_m": round(remaining, 3),
        "growth_rate_m_per_day": round(growth_rate_per_day, 6),
        "adjusted_growth_rate_m_per_quarter": rate_quarter,
    }


def _json_payload_field(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _dict_get(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _haversine_m(anchor: Any, shutter: Any) -> float | None:
    if not isinstance(anchor, dict) or not isinstance(shutter, dict):
        return None
    lat1 = to_float(anchor.get("latitude"))
    lon1 = to_float(anchor.get("longitude"))
    lat2 = to_float(shutter.get("latitude"))
    lon2 = to_float(shutter.get("longitude"))
    if None in {lat1, lon1, lat2, lon2}:
        return None
    radius = 6371000.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    d_phi = math.radians(float(lat2) - float(lat1))
    d_lambda = math.radians(float(lon2) - float(lon1))
    h = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def _detect_snapshot(
    *,
    original_path: Path,
    payload: dict[str, Any],
    image_width: int,
    image_height: int,
    free_vision_config: dict[str, Any],
    yolo_raw: dict[str, Any],
) -> dict[str, Any]:
    mock_payload = payload.get("mock_detection_payload")
    if mock_payload:
        if isinstance(mock_payload, str):
            try:
                mock_payload = json.loads(mock_payload)
            except json.JSONDecodeError:
                mock_payload = {}
        result = normalize_detection_payload(
            mock_payload,
            image_width=image_width,
            image_height=image_height,
            source_internal="mock_detection",
        )
        result["pipeline_status"] = "MOCK_DETECTION_USED"
        result["provider_status_redacted"] = [{"role": "mock", "status": "MOCK_DETECTION_USED", "configured": True}]
        result["provider_order"] = ["mock"]
        result = _filter_to_single_class_pohon_sono(result)
        return result
    return _single_class_detection_from_yolo(
        yolo_raw=yolo_raw,
        image_width=image_width,
        image_height=image_height,
    )


def _single_class_detection_from_yolo(*, yolo_raw: dict[str, Any], image_width: int, image_height: int) -> dict[str, Any]:
    detections = [
        dict(item)
        for item in yolo_raw.get("detections", [])
        if isinstance(item, dict) and str(item.get("class_name") or "") == "pohon_sono"
    ]
    model_ready = str(yolo_raw.get("status") or "") in {
        "YOLOV8_SINGLE_CLASS_POHON_SONO_READY",
        "YOLOV8_POHON_SONO_READY",
        "YOLOV8_MODEL_READY_CLASS_MAPPING_REVIEW_REQUIRED",
    }
    status = str(yolo_raw.get("status") or "YOLO_MODEL_NOT_READY")
    if not model_ready:
        status = "YOLO_MODEL_NOT_READY" if status in {"", "AI_MODEL_NOT_READY"} else status
    return {
        "status": status,
        "pipeline_status": "PLAN_C_SINGLE_CLASS_YOLOV8_RUNTIME",
        "runtime_mode": "PLAN_C_SINGLE_CLASS_POHON_SONO",
        "detector": "YOLOv8",
        "yolo_mode": "single_class",
        "model_policy": "single_class_pohon_sono",
        "active_detection_target": "pohon_sono",
        "active_class_names": ["pohon_sono"],
        "multi_class_runtime": False,
        "conductor_detection_enabled": False,
        "structure_detection_enabled": False,
        "conductor_required_for_detection": False,
        "detections": detections,
        "detection_count": len(detections),
        "image_width": image_width,
        "image_height": image_height,
        "tree_species_status": "pohon_sono" if detections else "unknown",
        "conductor_status": "manual/reference only",
        "structure_status": "manual/reference only",
        "zone_status": "manual_review_required",
        "operator_detection_label": "Detection",
        "operator_output_format": "YOLOv8 single-class",
        "review_status": "MANUAL_REVIEW_REQUIRED" if not detections else "REVIEW",
        "manual_review_required": True,
        "warnings": list(yolo_raw.get("warnings") or []),
        "limitations": [
            "Runtime ini hanya memakai bounding box YOLOv8 untuk pohon_sono.",
            "Konduktor dan struktur penyangga hanya konteks manual/reference, bukan class YOLO aktif.",
        ],
    }


def _filter_to_single_class_pohon_sono(result: dict[str, Any]) -> dict[str, Any]:
    detections = [
        dict(item)
        for item in result.get("detections", [])
        if isinstance(item, dict) and str(item.get("class_name") or "") == "pohon_sono"
    ]
    result.update(
        {
            "runtime_mode": "PLAN_C_SINGLE_CLASS_POHON_SONO",
            "detector": "YOLOv8",
            "yolo_mode": "single_class",
            "model_policy": "single_class_pohon_sono",
            "active_detection_target": "pohon_sono",
            "active_class_names": ["pohon_sono"],
            "multi_class_runtime": False,
            "conductor_detection_enabled": False,
            "structure_detection_enabled": False,
            "conductor_required_for_detection": False,
            "detections": detections,
            "detection_count": len(detections),
            "operator_output_format": "YOLOv8 single-class",
            "tree_species_status": "pohon_sono" if detections else "unknown",
            "conductor_status": "manual/reference only",
            "structure_status": "manual/reference only",
            "manual_review_required": True,
        }
    )
    return result


def _restore_single_class_runtime_detection(result: dict[str, Any], *, yolo_raw: dict[str, Any]) -> dict[str, Any]:
    detections = [
        dict(item)
        for item in result.get("detections", [])
        if isinstance(item, dict) and str(item.get("class_name") or "") == "pohon_sono"
    ]
    model_status = str(yolo_raw.get("status") or result.get("status") or "YOLO_MODEL_NOT_READY")
    result.update(
        {
            "status": model_status,
            "pipeline_status": "PLAN_C_SINGLE_CLASS_YOLOV8_RUNTIME",
            "runtime_mode": "PLAN_C_SINGLE_CLASS_POHON_SONO",
            "detector": "YOLOv8",
            "yolo_mode": "single_class",
            "model_policy": "single_class_pohon_sono",
            "active_detection_target": "pohon_sono",
            "active_class_names": ["pohon_sono"],
            "multi_class_runtime": False,
            "conductor_detection_enabled": False,
            "structure_detection_enabled": False,
            "conductor_required_for_detection": False,
            "detections": detections,
            "detection_count": len(detections),
            "tree_species_status": "pohon_sono" if detections else "unknown",
            "conductor_status": "manual/reference only",
            "structure_status": "manual/reference only",
            "zone_status": "manual_review_required",
            "operator_output_format": "YOLOv8 single-class",
            "review_status": "MANUAL_REVIEW_REQUIRED" if not detections else "REVIEW",
            "manual_review_required": True,
        }
    )
    return result


def _apply_ai_consensus_tree_bbox(
    detection_result: dict[str, Any],
    *,
    ai_raw: dict[str, Any],
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    detections = [
        dict(item)
        for item in detection_result.get("detections", [])
        if isinstance(item, dict) and str(item.get("class_name") or "") == "pohon_sono"
    ]
    chosen_source = str(ai_raw.get("chosen_bbox_source") or ("YOLOV8_LOCAL" if detections else "NONE"))
    if detections:
        detection_result.update(
            {
                "detections": detections,
                "detection_count": len(detections),
                "final_detection_source": "YOLOV8_LOCAL",
                "tree_species_status": "pohon_sono",
            }
        )
        return detection_result

    chosen_bbox = ai_raw.get("chosen_bbox")
    if chosen_source == "AI_CONSENSUS" and isinstance(chosen_bbox, list):
        validity = validate_ai_bbox({"bbox_xyxy": chosen_bbox}, image_width, image_height)
        if validity.get("valid"):
            provider = str(ai_raw.get("summary", {}).get("provider") or "ai_consensus")
            detection = {
                "id": 0,
                "class_id": 0,
                "class_name": "pohon_sono",
                "operator_label": "pohon_sono",
                "confidence": _ai_consensus_confidence(ai_raw),
                "bbox_format": "xyxy",
                "bbox_xyxy": validity["bbox_xyxy"],
                "source": "ai_consensus_tree_bbox_review",
                "label": "AI+YOLOv8 pohon_sono review",
                "review_status": "REVIEW",
                "reason": "AI consensus bbox dipakai hanya karena YOLOv8 lokal tidak menghasilkan bbox pohon_sono.",
            }
            detection_result.update(
                {
                    "detections": [detection],
                    "detection_count": 1,
                    "final_detection_source": "AI_CONSENSUS",
                    "tree_species_status": "pohon_sono",
                    "manual_review_required": True,
                    "ai_bbox_provider": provider,
                }
            )
            return detection_result

    detection_result.update(
        {
            "detections": [],
            "detection_count": 0,
            "final_detection_source": "NONE",
            "tree_species_status": "unknown",
            "manual_review_required": True,
        }
    )
    return detection_result


def _finalize_system_c_zone_decision(
    *,
    detections: list[dict[str, Any]],
    geometry: dict[str, Any],
    growth: dict[str, Any],
    ai_raw: dict[str, Any],
    metadata: dict[str, Any],
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    zone_bands = _build_heuristic_zone_bands(image_width, image_height)
    manual_inputs = metadata.get("manual_inputs") if isinstance(metadata.get("manual_inputs"), dict) else {}
    manual_clearance = to_float((manual_inputs or {}).get("manual_clearance_m"))
    tree_bbox = _best_tree_bbox(detections)
    zone_method = "heuristic_band_without_manual_clearance"
    zone_final = "REVIEW_REQUIRED"
    manual_review_required = True
    geometry_status = str(geometry.get("geometry_status") or "INSUFFICIENT_GEOMETRY_DATA")

    if manual_clearance is not None:
        risk_status, prediction_window = _risk_from_manual_clearance(manual_clearance)
        zone_method = "manual_clearance"
        zone_final = risk_status
        manual_review_required = bool(geometry.get("manual_review_required"))
    elif tree_bbox:
        risk_status, prediction_window, zone_final = _risk_from_tree_bbox(tree_bbox, zone_bands, growth)
        geometry_status = "HEURISTIC_ZONE_REVIEW_REQUIRED"
        ai_zone = str(ai_raw.get("risk_zone_guess") or ai_raw.get("summary", {}).get("risk_zone_guess") or "REVIEW_REQUIRED")
        if ai_zone == zone_final and ai_raw.get("summary", {}).get("ok_count", 0):
            zone_method = "ai_assisted_zone_consensus"
    else:
        risk_status = "DATA_TIDAK_CUKUP"
        prediction_window = "data tidak cukup"
        geometry_status = "DATA_TIDAK_CUKUP_POHON_TIDAK_TERDETEKSI"

    return {
        "risk_status": risk_status,
        "prediction_window": prediction_window,
        "zone_method": zone_method,
        "zone_final": zone_final,
        "zone_bands": zone_bands,
        "geometry_updates": {
            "geometry_status": geometry_status,
            "risk_status": risk_status,
            "zone_status": "rendered",
            "zone_overlay_status": "ZONE_OVERLAY_RENDERED",
            "zone_method": zone_method,
            "zone_final": zone_final,
            "zone_bands": zone_bands,
            "clearance_estimate_m": geometry.get("clearance_estimate_m"),
            "manual_review_required": manual_review_required,
            "conductor_required_for_detection": False,
        },
        "growth_updates": {
            "risk_status": risk_status,
            "prediction_window": prediction_window,
            "prediction_status": "HEURISTIC_ZONE_PREDICTION_READY" if tree_bbox or manual_clearance is not None else "DATA_TIDAK_CUKUP",
        },
        "detection_updates": {
            "zone_overlay_status": "ZONE_OVERLAY_RENDERED",
            "zone_method": zone_method,
            "zone_final": zone_final,
            "manual_review_required": manual_review_required,
            "conductor_required_for_detection": False,
        },
    }


def _build_heuristic_zone_bands(image_width: int, image_height: int) -> list[dict[str, Any]]:
    height = max(int(image_height or 0), 1)
    width = max(int(image_width or 0), 1)
    tebang_y2 = int(round(height * 0.34))
    pantau_y2 = int(round(height * 0.67))
    return [
        {"zone": "ZONA_TEBANG", "label": "ZONA TEBANG", "x1": 0, "y1": 0, "x2": width, "y2": tebang_y2},
        {"zone": "ZONA_PANTAU", "label": "ZONA PANTAU", "x1": 0, "y1": tebang_y2, "x2": width, "y2": pantau_y2},
        {"zone": "ZONA_AMAN", "label": "ZONA AMAN", "x1": 0, "y1": pantau_y2, "x2": width, "y2": height},
    ]


def _risk_from_tree_bbox(
    bbox: list[float],
    zone_bands: list[dict[str, Any]],
    growth: dict[str, Any],
) -> tuple[str, str, str]:
    x1, y1, x2, y2 = [float(value) for value in bbox]
    del x1, x2
    tebang_y2 = float(zone_bands[0]["y2"])
    pantau_y2 = float(zone_bands[1]["y2"])
    if y1 <= tebang_y2:
        return "ZONA_TEBANG", "0-3 bulan", "ZONA_TEBANG"
    if y1 <= pantau_y2 or y2 <= pantau_y2:
        rate = to_float(growth.get("growth_rate_m_per_quarter"))
        return "ZONA_PANTAU", "3-6 bulan" if rate is None or rate > 0 else "6-9 bulan", "ZONA_PANTAU"
    return "ZONA_AMAN", ">12 bulan", "ZONA_AMAN"


def _risk_from_manual_clearance(clearance_m: float) -> tuple[str, str]:
    if clearance_m <= 3.0:
        return "ZONA_TEBANG", "0-3 bulan"
    if clearance_m <= 4.5:
        return "ZONA_PANTAU", "3-6 bulan"
    return "ZONA_AMAN", ">12 bulan"


def _best_tree_bbox(detections: list[dict[str, Any]]) -> list[float] | None:
    candidates = []
    for item in detections:
        if not isinstance(item, dict) or str(item.get("class_name") or "") != "pohon_sono":
            continue
        bbox = item.get("bbox_xyxy")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            candidates.append((float(item.get("confidence") or 0.0), [float(value) for value in bbox]))
        except (TypeError, ValueError):
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _ai_consensus_confidence(ai_raw: dict[str, Any]) -> float:
    provider_results = ai_raw.get("provider_results")
    if not isinstance(provider_results, list):
        return 0.5
    values = [float(item.get("confidence") or 0.0) for item in provider_results if isinstance(item, dict) and item.get("status") == "OK"]
    return round(max(values), 4) if values else 0.5


def _adjust_growth_for_species(growth: dict[str, Any], detection_result: dict[str, Any]) -> dict[str, Any]:
    species = detection_result.get("tree_species_status")
    if species != "pohon_non_sono":
        return growth
    adjusted = dict(growth)
    adjusted["growth_profile_status"] = "GROWTH_PROFILE_READY_PROXY"
    adjusted["data_source_type"] = "generic_vegetation_proxy"
    adjusted["observed_or_proxy"] = "proxy"
    adjusted["confidence_level"] = "generic_proxy_requires_field_validation"
    limitations = list(adjusted.get("limitations") or [])
    limitations.append("Pohon terdeteksi sebagai pohon_non_sono; growth profile pohon_sono tidak diklaim sebagai identifikasi final.")
    adjusted["limitations"] = limitations
    source = dict(adjusted.get("source_summary") or {})
    source["species_handling"] = "generic_vegetation_proxy"
    adjusted["source_summary"] = source
    return adjusted


def _operator_detections(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = {
        "class_id",
        "class_name",
        "bbox_format",
        "bbox_xyxy",
        "confidence",
        "operator_label",
        "species_guess",
        "is_target_species",
        "review_status",
        "reason",
    }
    return [{key: value for key, value in detection.items() if key in allowed} for detection in detections if isinstance(detection, dict)]


def _read_image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return 0, 0


def _disabled_legacy_visual_validator(original_path: Path, *, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "VISION_PROVIDER_DISABLED",
        "enabled": False,
        "visual_quality": "not_run",
        "object_visibility": "not_run",
        "retake_recommendation": "Detection summary dan geometry digunakan untuk review operator.",
        "short_validation_summary": "External visual validation tidak dijalankan pada mode free-only tanpa konfigurasi lokal.",
        "image_path": relative_to_project(original_path),
        "metadata_keys": sorted(metadata.keys()),
        "no_secret_logged": True,
    }
