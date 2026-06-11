"""Snapshot processing orchestration for Plan C."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Any

from .plan_c_ai_validator import validate_snapshot_with_ai
from .plan_c_geometry import DEFAULT_GEOMETRY_PARAMETERS, compute_plan_c_geometry
from .plan_c_growth_model import build_growth_summary, load_growth_profile
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


def process_plan_c_snapshot(session_id: str, *, image_file: Any | None, payload: dict[str, Any]) -> dict[str, Any]:
    folder = ensure_session_dir(session_id)
    original_path = folder / "original.jpg"
    annotated_path = folder / "annotated.jpg"
    _save_snapshot_image(original_path, image_file=image_file, payload=payload)

    metadata = load_plan_c_metadata(session_id)
    metadata.update(_build_snapshot_metadata(session_id, payload, original_path))
    metadata["status"] = "PLAN_C_PROCESSING"
    metadata["snapshot_status"] = "PLAN_C_SNAPSHOT_ACCEPTED"
    metadata["processing_status"] = "PLAN_C_PROCESSING"
    save_plan_c_metadata(session_id, metadata)

    yolo_raw = run_yolo_post_capture(original_path, annotated_path)
    write_json(session_file(session_id, "yolo_raw.json"), yolo_raw)

    ai_raw = validate_snapshot_with_ai(original_path, metadata=metadata)
    write_json(session_file(session_id, "ai_raw.json"), ai_raw)

    geometry = compute_plan_c_geometry(
        yolo_raw.get("detections", []),
        metadata=metadata,
        manual_inputs=metadata.get("manual_inputs", {}),
    )
    write_json(session_file(session_id, "geometry.json"), geometry)

    capture_month = _capture_month(metadata.get("snapshot_captured_at"))
    growth = build_growth_summary(
        clearance_m=geometry.get("clearance_estimate_m"),
        threshold_m=DEFAULT_GEOMETRY_PARAMETERS["vegetation_clearance_threshold_m"],
        month=capture_month,
    )
    risk_status = geometry.get("risk_status") or "DATA_TIDAK_CUKUP"
    prediction_window = growth.get("prediction_window") or "data tidak cukup"
    if risk_status == "DATA_TIDAK_CUKUP":
        prediction_window = "data tidak cukup"

    result = _build_result_payload(
        session_id=session_id,
        metadata=metadata,
        original_path=original_path,
        annotated_path=annotated_path,
        yolo_raw=yolo_raw,
        ai_raw=ai_raw,
        geometry=geometry,
        growth=growth,
        risk_status=risk_status,
        prediction_window=prediction_window,
    )
    write_json(session_file(session_id, "result.json"), result)

    record = _build_record(result)
    append_status = append_plan_c_record(record)
    marker_status = append_marker(_build_marker(result))

    developer = _build_developer_payload(
        session_id=session_id,
        metadata=metadata,
        yolo_raw=yolo_raw,
        ai_raw=ai_raw,
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
        "result_url": f"/plan-c/result/{session_id}",
        "processing_url": f"/plan-c/processing/{session_id}",
        "developer_url": f"/plan-c/developer/{session_id}",
        "risk_status": result["risk_status"],
        "prediction_window": result["prediction_window"],
        "append_status": append_status,
        "marker_status": marker_status,
    }


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


def _build_snapshot_metadata(session_id: str, payload: dict[str, Any], original_path: Path) -> dict[str, Any]:
    gps = _extract_gps(payload)
    manual_inputs = {
        "manual_distance_m": to_float(payload.get("manual_distance_m")),
        "manual_tree_height_m": to_float(payload.get("manual_tree_height_m")),
        "manual_clearance_m": to_float(payload.get("manual_clearance_m")),
        "manual_conductor_height_m": to_float(payload.get("manual_conductor_height_m")),
    }
    return {
        "session_id": session_id,
        "snapshot_captured_at": utc_now_iso(),
        "operator_note": str(payload.get("operator_note") or payload.get("notes") or "").strip(),
        "gps": gps,
        "gps_status": "GPS_VALID" if gps.get("gps_valid") else "NO_GPS_NO_MARKER",
        "manual_inputs": manual_inputs,
        "original_path": str(original_path),
    }


def _extract_gps(payload: dict[str, Any]) -> dict[str, Any]:
    latitude = to_float(payload.get("latitude") or payload.get("lat"))
    longitude = to_float(payload.get("longitude") or payload.get("lon") or payload.get("lng"))
    accuracy = to_float(payload.get("gps_accuracy_m") or payload.get("accuracy"))
    return {
        "latitude": latitude,
        "longitude": longitude,
        "gps_accuracy_m": accuracy,
        "gps_valid": latitude is not None and longitude is not None,
        "source": "browser_gps_client",
    }


def _build_result_payload(
    *,
    session_id: str,
    metadata: dict[str, Any],
    original_path: Path,
    annotated_path: Path,
    yolo_raw: dict[str, Any],
    ai_raw: dict[str, Any],
    geometry: dict[str, Any],
    growth: dict[str, Any],
    risk_status: str,
    prediction_window: str,
) -> dict[str, Any]:
    gps = metadata.get("gps", {})
    return {
        "status": "PLAN_C_RESULT_READY",
        "session_id": session_id,
        "created_at": utc_now_iso(),
        "risk_status": risk_status,
        "prediction_window": prediction_window,
        "tree_height_estimate_m": geometry.get("tree_height_estimate_m"),
        "clearance_estimate_m": geometry.get("clearance_estimate_m"),
        "manual_review_required": bool(
            geometry.get("manual_review_required") or yolo_raw.get("manual_review_required") or risk_status == "DATA_TIDAK_CUKUP"
        ),
        "yolo_status": yolo_raw.get("status"),
        "yolo_summary": {
            "status": yolo_raw.get("status"),
            "detection_count": yolo_raw.get("detection_count", 0),
            "manual_review_required": yolo_raw.get("manual_review_required", True),
            "model_path": yolo_raw.get("model_path", ""),
        },
        "ai_validator_status": ai_raw.get("status"),
        "ai_validation_summary": {
            "status": ai_raw.get("status"),
            "visual_quality": ai_raw.get("visual_quality"),
            "object_visibility": ai_raw.get("object_visibility"),
            "retake_recommendation": ai_raw.get("retake_recommendation"),
            "short_validation_summary": ai_raw.get("short_validation_summary"),
        },
        "gps_summary": gps,
        "geometry_status": geometry.get("geometry_status"),
        "growth_profile_status": growth.get("growth_profile_status"),
        "growth_rate_m_per_quarter": growth.get("growth_rate_m_per_quarter"),
        "data_source_type": growth.get("data_source_type"),
        "observed_or_proxy": growth.get("observed_or_proxy"),
        "confidence_level": growth.get("confidence_level"),
        "limitations": growth.get("limitations", []),
        "growth_source_summary": growth.get("source_summary", {}),
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
        "yolo_status": result.get("yolo_status"),
        "ai_validator_status": result.get("ai_validator_status"),
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
        "risk_status": result.get("risk_status"),
        "prediction_window": result.get("prediction_window"),
        "result_url": result.get("links", {}).get("result"),
        "developer_url": result.get("links", {}).get("developer"),
        "source": "plan_c_snapshot",
    }


def _build_developer_payload(
    *,
    session_id: str,
    metadata: dict[str, Any],
    yolo_raw: dict[str, Any],
    ai_raw: dict[str, Any],
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
            "AI validator tidak menggantikan YOLO atau Python geometry.",
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
