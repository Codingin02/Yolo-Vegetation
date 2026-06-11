"""Processor for Plan C upload image mode."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .plan_c_ai_model_runtime import get_plan_c_ai_model_status, predict_plan_c_ai_objects, save_annotated_image
from .plan_c_ai_validator import validate_snapshot_with_ai
from .plan_c_geometry import compute_plan_c_geometry
from .plan_c_growth_model import build_growth_summary
from .plan_c_storage import (
    append_marker,
    append_plan_c_record,
    is_valid_gps,
    read_json,
    relative_to_project,
    session_file,
    to_float,
    utc_now_iso,
    write_json,
)
from .plan_c_upload_storage import SOURCE_MODE, load_upload_metadata, update_upload_metadata
from .plan_c_zone_engine import classify_plan_c_zone


def process_upload_session(session_id: str) -> dict[str, Any]:
    metadata = load_upload_metadata(session_id)
    if not metadata:
        return {"ok": False, "status": "PLAN_C_UPLOAD_SESSION_NOT_FOUND", "http_status": 404}

    existing = read_json(session_file(session_id, "result.json"), default={}) or {}
    if existing and metadata.get("upload_record_appended"):
        return {
            "ok": True,
            "status": "DUPLICATE_IGNORED",
            "session_id": session_id,
            "result_ready": True,
            "result_url": f"/plan-c/upload/result/{session_id}",
            "result": existing,
            "http_status": 200,
        }

    update_upload_metadata(
        session_id,
        {
            "detection_status": "PLAN_C_UPLOAD_PROCESSING",
            "manual_process_required": False,
            "processed_at": utc_now_iso(),
        },
    )
    original_path = session_file(session_id, "original.jpg")
    annotated_path = session_file(session_id, "annotated.jpg")

    model_raw = predict_plan_c_ai_objects(original_path)
    detections = list(model_raw.get("detections") or [])
    model_status = get_plan_c_ai_model_status()
    ai_raw = validate_snapshot_with_ai(original_path, metadata=metadata)
    geometry = compute_plan_c_geometry(detections, metadata=metadata)
    zone = classify_plan_c_zone(geometry, detections, ai_validator=ai_raw)
    clearance_m = zone.get("clearance_m")
    growth = build_growth_summary(clearance_m=clearance_m)
    warnings = _dedupe(
        [
            *[str(item) for item in model_raw.get("warnings", [])],
            *[str(item) for item in geometry.get("warnings", [])],
            *[str(item) for item in zone.get("warnings", [])],
        ]
    )
    prediction_window = growth.get("prediction_window") or "data tidak cukup"
    if zone.get("risk_status") == "DATA_TIDAK_CUKUP":
        prediction_window = "data tidak cukup"
    summary = {
        "risk_status": zone.get("risk_status", "DATA_TIDAK_CUKUP"),
        "prediction_window": prediction_window,
        "manual_review_required": bool(zone.get("manual_review_required", True)),
        "warnings": warnings,
    }
    annotation = save_annotated_image(original_path, annotated_path, detections, summary=summary)

    lat = metadata.get("latitude")
    lon = metadata.get("longitude")
    gps_valid = is_valid_gps(lat, lon)
    gps_status = metadata.get("gps_status") if gps_valid else "GPS_NOT_AVAILABLE"
    result = {
        "ok": True,
        "status": "PLAN_C_UPLOAD_RESULT_READY",
        "session_id": session_id,
        "source_mode": SOURCE_MODE,
        "model_user_name": "AI Vision Detector",
        "model_status": model_status.get("status"),
        "detection_status": model_raw.get("status"),
        "detected_objects": _detected_summary(detections),
        "detection_count": len(detections),
        "risk_status": zone.get("risk_status", "DATA_TIDAK_CUKUP"),
        "zone": zone.get("zone", "DATA_TIDAK_CUKUP"),
        "prediction_window": prediction_window,
        "clearance_m": clearance_m,
        "clearance_estimate_m": clearance_m,
        "tree_height_estimate_m": geometry.get("tree_height_estimate_m"),
        "growth_profile_status": growth.get("growth_profile_status"),
        "growth_rate_m_per_quarter": growth.get("growth_rate_m_per_quarter"),
        "gps_status": gps_status,
        "latitude": lat if gps_valid else None,
        "longitude": lon if gps_valid else None,
        "accuracy_m": metadata.get("accuracy_m") if gps_valid else None,
        "ai_validator_status": ai_raw.get("status"),
        "ai_validator_summary": ai_raw.get("short_validation_summary"),
        "manual_review_required": bool(zone.get("manual_review_required", True)),
        "warnings": warnings,
        "links": {
            "result": f"/plan-c/upload/result/{session_id}",
            "developer": f"/plan-c/upload/developer/{session_id}",
            "map": "/plan-c/map" if gps_valid else "",
        },
        "files": {
            "original": relative_to_project(original_path),
            "annotated": relative_to_project(annotated_path),
            "result": relative_to_project(session_file(session_id, "result.json")),
        },
        "not_final_pln_accuracy_claim": True,
    }
    developer = {
        "session_id": session_id,
        "metadata": metadata,
        "model_registry": model_status,
        "ai_model_raw": model_raw,
        "ai_raw": ai_raw,
        "geometry": geometry,
        "growth": growth,
        "zone": zone,
        "annotation": annotation,
        "class_weakness_warning": "CONDUCTOR_CLASS_WEAK_VALIDATION_SET_SMALL",
        "file_paths": {
            "metadata": relative_to_project(session_file(session_id, "metadata.json")),
            "result": relative_to_project(session_file(session_id, "result.json")),
            "developer": relative_to_project(session_file(session_id, "developer.json")),
            "ai_model_raw": relative_to_project(session_file(session_id, "ai_model_raw.json")),
            "yolo_raw": relative_to_project(session_file(session_id, "yolo_raw.json")),
            "ai_raw": relative_to_project(session_file(session_id, "ai_raw.json")),
            "geometry": relative_to_project(session_file(session_id, "geometry.json")),
            "growth": relative_to_project(session_file(session_id, "growth.json")),
            "original": relative_to_project(original_path),
            "annotated": relative_to_project(annotated_path),
        },
    }

    write_json(session_file(session_id, "ai_model_raw.json"), model_raw)
    write_json(session_file(session_id, "yolo_raw.json"), model_raw)
    write_json(session_file(session_id, "ai_raw.json"), ai_raw)
    write_json(session_file(session_id, "geometry.json"), geometry)
    write_json(session_file(session_id, "growth.json"), growth)
    write_json(session_file(session_id, "result.json"), result)
    write_json(session_file(session_id, "developer.json"), developer)
    append_status = _append_upload_outputs(session_id, metadata, result, detections)
    update_upload_metadata(
        session_id,
        {
            "detection_status": "PLAN_C_UPLOAD_RESULT_READY",
            "result_status": result.get("risk_status"),
            "upload_record_appended": append_status.get("record_appended"),
            "upload_marker_status": append_status.get("marker", {}).get("status"),
            "updated_at": utc_now_iso(),
        },
    )
    return {
        "ok": True,
        "status": "PLAN_C_UPLOAD_RESULT_READY",
        "session_id": session_id,
        "result_ready": True,
        "result_url": f"/plan-c/upload/result/{session_id}",
        "result": result,
        "append_status": append_status,
        "http_status": 200,
    }


def build_upload_status(session_id: str) -> dict[str, Any]:
    metadata = load_upload_metadata(session_id)
    result = read_json(session_file(session_id, "result.json"), default={}) or {}
    if not metadata:
        return {"ok": False, "status": "PLAN_C_UPLOAD_SESSION_NOT_FOUND", "session_id": session_id}
    return {
        "ok": True,
        "session_id": session_id,
        "status": result.get("status") or metadata.get("upload_status") or "UPLOAD_ACCEPTED_DETECTION_PENDING",
        "result_ready": bool(result),
        "metadata": metadata,
    }


def _append_upload_outputs(session_id: str, metadata: dict[str, Any], result: dict[str, Any], detections: list[dict[str, Any]]) -> dict[str, Any]:
    if metadata.get("upload_record_appended"):
        return {"record_appended": False, "record": {"status": "DUPLICATE_IGNORED"}, "marker": {"status": "DUPLICATE_IGNORED"}}
    detected_classes = sorted({str(item.get("class_name")) for item in detections if item.get("class_name")})
    record = {
        "record_id": f"{session_id}:upload",
        "timestamp": utc_now_iso(),
        "created_at": utc_now_iso(),
        "session_id": session_id,
        "source_mode": SOURCE_MODE,
        "point_id": metadata.get("point_id"),
        "operator_name": metadata.get("operator_name"),
        "gps_status": result.get("gps_status"),
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "accuracy_m": result.get("accuracy_m"),
        "gps_accuracy_m": result.get("accuracy_m"),
        "model_status": result.get("model_status"),
        "detected_classes": detected_classes,
        "risk_status": result.get("risk_status"),
        "zone": result.get("zone"),
        "clearance_m": result.get("clearance_m"),
        "prediction_window": result.get("prediction_window"),
        "manual_review_required": result.get("manual_review_required"),
        "warnings": result.get("warnings"),
        "ai_validator_status": result.get("ai_validator_status"),
        "geometry_status": read_json(session_file(session_id, "geometry.json"), default={}).get("geometry_status"),
        "growth_profile_status": result.get("growth_profile_status"),
        "growth_rate_m_per_quarter": result.get("growth_rate_m_per_quarter"),
        "data_source_type": "proxy",
        "original_path": relative_to_project(session_file(session_id, "original.jpg")),
        "original_image_path": relative_to_project(session_file(session_id, "original.jpg")),
        "annotated_path": relative_to_project(session_file(session_id, "annotated.jpg")),
        "annotated_image_path": relative_to_project(session_file(session_id, "annotated.jpg")),
        "result_path": relative_to_project(session_file(session_id, "result.json")),
    }
    record_status = append_plan_c_record(record)
    marker = append_marker(
        {
            "session_id": session_id,
            "source_mode": SOURCE_MODE,
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "accuracy_m": result.get("accuracy_m"),
            "risk_status": result.get("risk_status"),
            "prediction_window": result.get("prediction_window"),
            "result_url": f"/plan-c/upload/result/{session_id}",
            "created_at": utc_now_iso(),
        }
    )
    return {"record_appended": True, "record": record_status, "marker": marker}


def _detected_summary(detections: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for item in detections:
        class_name = str(item.get("class_name") or "unknown")
        counts[class_name] = counts.get(class_name, 0) + 1
    return counts


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result
