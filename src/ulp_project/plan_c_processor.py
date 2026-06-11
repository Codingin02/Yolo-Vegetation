"""Snapshot processing orchestration for Plan C."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
import re
from typing import Any

from .plan_c_free_vision_config import load_free_vision_config, redact_config
from .plan_c_free_vision_detector import detect_yolo_compatible_from_snapshot
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
    detection_result = detect_yolo_compatible_from_snapshot(
        original_path,
        image_width=image_width,
        image_height=image_height,
        config=free_vision_config,
        yolo_result=yolo_raw,
    )
    render_status = render_yolo_compatible_annotation(original_path, annotated_path, detection_result.get("detections", []))

    ai_raw = _disabled_legacy_visual_validator(original_path, metadata=metadata)
    write_json(session_file(session_id, "ai_raw.json"), ai_raw)

    geometry = compute_plan_c_geometry(
        detection_result.get("detections", []),
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
    }
    return {
        "session_id": session_id,
        "point_id": str(payload.get("point_id") or "pohon_sono").strip() or "pohon_sono",
        "idempotency_key": idempotency_key,
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
    gps_valid = latitude is not None and longitude is not None
    raw_status = str(payload.get("gps_status") or "").strip()
    gps_status = raw_status if raw_status else "GPS_NOT_READY"
    gps_quality_status = "GPS_NOT_READY"
    if gps_valid:
        gps_status = "GPS_READY"
        gps_quality_status = "GPS_LOW_ACCURACY_EVIDENCE_ONLY" if accuracy is not None and accuracy > 20 else "GPS_ACCURACY_ACCEPTED"
    return {
        "latitude": latitude,
        "longitude": longitude,
        "gps_accuracy_m": accuracy,
        "gps_valid": gps_valid,
        "gps_status": gps_status,
        "gps_quality_status": gps_quality_status,
        "gps_source": "GPS_SOURCE_BROWSER" if gps_valid else "GPS_SOURCE_UNAVAILABLE",
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
        "session_id": session_id,
        "point_id": metadata.get("point_id") or "pohon_sono",
        "idempotency_key": idempotency_key,
        "created_at": utc_now_iso(),
        "risk_status": risk_status,
        "prediction_window": prediction_window,
        "tree_height_estimate_m": geometry.get("tree_height_estimate_m"),
        "clearance_estimate_m": geometry.get("clearance_estimate_m"),
        "manual_review_required": bool(
            geometry.get("manual_review_required")
            or detection_result.get("manual_review_required")
            or risk_status == "DATA_TIDAK_CUKUP"
        ),
        "detection_status": detection_status,
        "detection_count": detection_count,
        "operator_detection_label": detection_result.get("operator_detection_label", "Detection"),
        "operator_output_format": detection_result.get("operator_output_format", "YOLO-compatible"),
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
        },
        "detection_summary": {
            "status": detection_status,
            "detection_count": detection_count,
            "operator_output_format": detection_result.get("operator_output_format", "YOLO-compatible"),
            "manual_review_required": detection_result.get("manual_review_required", True),
            "render_status": render_status.get("status"),
        },
        "gps_summary": gps,
        "gps_status": gps.get("gps_quality_status") or gps.get("gps_status") or "GPS_NOT_READY",
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
            "Detection adapter dan YOLO-compatible output tetap membutuhkan review lapangan.",
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
