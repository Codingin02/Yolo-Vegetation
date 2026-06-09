"""Native browser GPS/camera field session runtime."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .gps_reliability_policy import (
    compute_haversine_meters as assess_haversine_meters,
    distance_reliability as assess_distance_reliability,
    gps_accuracy_status as assess_gps_accuracy_status,
)
from .gps_truth_policy import format_coordinate_raw, select_best_gps_sample, validate_gps_evidence
from .growth_prediction_runtime import predict_growth_prior
from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT
from .progress5_4_field_runtime import (
    PROGRESS5_4_REPORT_COLUMNS,
    PROGRESS5_4_REPORT_CSV,
    ensure_progress5_4_report_schema,
    latest_progress5_4_measurement,
    process_progress5_4_realtime_frame,
)
from .realtime_stability_filter import apply_stability_filter
from .realtime_yolo_detection_pipeline import model_readiness_status, process_realtime_yolo_frame
from .runtime_yolo_status import resolve_vision_runtime_status, get_yolo_readiness_response
from .tree_detection_runtime import decode_frame_image_bytes, infer_tree_candidate, tree_model_status

SESSION_RUNTIME_DIR = PROJECT_ROOT / "data" / "runtime" / "field_sessions"
SESSION_MAP_DIR = PROJECT_ROOT / "data" / "runtime" / "field_maps"
SESSION_SMOKE_REPORT_CSV = PROJECT_ROOT / "outputs" / "reports" / "field_capture_smoke_autosave.csv"
SESSION_ERROR_DIR = PROJECT_ROOT / "data" / "runtime" / "session_errors"

FIELD_SESSION_REPORT_COLUMNS = [
    "session_id",
    "recording_status",
    "base_latitude",
    "base_longitude",
    "base_accuracy_m",
    "current_latitude",
    "current_longitude",
    "current_accuracy_m",
    "horizontal_distance_from_tree_m",
    "distance_reliability_status",
    "gps_accuracy_status",
    "gps_quality_reason",
    "foreground_recording_status",
    "visibility_state",
    "hidden_duration_ms",
    "browser_throttle_warning",
    "manual_input_status",
    "page_source",
    "result_page_url",
    "report_page_url",
    "idempotency_key",
    "capture_sequence",
    "source_mode",
    "gps_lat_raw",
    "gps_lon_raw",
    "base_latitude_raw",
    "base_longitude_raw",
    "current_latitude_raw",
    "current_longitude_raw",
    "gps_precision_status",
    "tree_model_status",
    "tree_confidence",
    "tree_bbox",
    "pole_model_status",
    "conductor_model_status",
    "growth_prior_status",
    "growth_year_m",
    "eta_3m_status",
    "spreadsheet_url",
]

for column in FIELD_SESSION_REPORT_COLUMNS:
    if column not in PROGRESS5_4_REPORT_COLUMNS:
        PROGRESS5_4_REPORT_COLUMNS.append(column)


@dataclass
class FieldSession:
    session_id: str
    point_id: str = "V001_pohon_sono"
    operator_name: str = ""
    started_at: str = ""
    stopped_at: str = ""
    session_status: str = "RECORDING_STOPPED"
    secure_context_status: str = "UNKNOWN"
    public_tunnel_status: str = "PUBLIC_TUNNEL_NOT_RUNNING"
    base_gps: dict[str, Any] = field(default_factory=dict)
    current_gps: dict[str, Any] = field(default_factory=dict)
    gps_history: list[dict[str, Any]] = field(default_factory=list)
    camera_status: str = "CAMERA_WAITING_PERMISSION"
    model_status: str = "MODEL_NOT_READY"
    latest_frame_status: dict[str, Any] = field(default_factory=dict)
    latest_measurement: dict[str, Any] = field(default_factory=dict)
    latest_result: dict[str, Any] = field(default_factory=dict)
    latest_report: dict[str, Any] = field(default_factory=dict)
    visibility_state: str = "visible"
    foreground_recording_status: str = "FOREGROUND_RECORDING_REQUIRED"
    hidden_started_at: str = ""
    hidden_duration_ms: int = 0
    frame_loop_paused_due_to_hidden: bool = False
    browser_throttle_warning: str = ""
    start_idempotency_key: str = ""
    latest_shutter_idempotency_key: str = ""
    capture_sequence: int = 0
    source_mode: str = "LIVE_OPERATOR"
    reason_codes: list[str] = field(default_factory=lambda: ["FOREGROUND_RECORDING_REQUIRED"])


_SESSIONS: dict[str, FieldSession] = {}
_LATEST_SESSION_ID = ""
_LATEST_MANUAL_INPUT: dict[str, Any] = {"status": "NO_MANUAL_INPUT_YET"}
_START_IDEMPOTENCY: dict[str, str] = {}
_SHUTTER_IDEMPOTENCY: dict[str, dict[str, Any]] = {}
_LAST_SHUTTER_FINGERPRINT: dict[str, dict[str, Any]] = {}


def gps_accuracy_status(accuracy_m: Any) -> dict[str, Any]:
    return assess_gps_accuracy_status(accuracy_m)


def compute_haversine_meters(base: dict[str, Any] | None, current: dict[str, Any] | None) -> float | None:
    return assess_haversine_meters(base, current)


def distance_reliability(base: dict[str, Any] | None, current: dict[str, Any] | None) -> dict[str, Any]:
    return assess_distance_reliability(base, current)


def normalize_gps(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _coerce_gps_payload(payload)
    gps = {
        "latitude": _to_float(_first_present(payload, "latitude", "gps_lat", "lat", "base_latitude", "current_latitude")),
        "longitude": _to_float(_first_present(payload, "longitude", "gps_lon", "lon", "base_longitude", "current_longitude")),
        "accuracy": _to_float(_first_present(payload, "accuracy", "accuracy_m", "gps_accuracy_m", "base_accuracy_m", "current_accuracy_m")),
        "altitude": _to_float(payload.get("altitude")),
        "altitudeAccuracy": _to_float(_first_present(payload, "altitudeAccuracy", "altitude_accuracy")),
        "heading": _to_float(payload.get("heading")),
        "speed": _to_float(payload.get("speed")),
        "timestamp": payload.get("timestamp") or datetime.now().isoformat(),
        "source": payload.get("source") or payload.get("gps_source") or "GPS_SOURCE_BROWSER",
    }
    truth = validate_gps_evidence(gps)
    gps.update(
        {
            "latitude_raw": truth["latitude_raw"],
            "longitude_raw": truth["longitude_raw"],
            "gps_precision_status": truth["gps_precision_status"],
            "gps_marker_status": truth["status"],
            "gps_quality_reasons": truth["gps_quality_reasons"],
        }
    )
    return gps


def _coerce_gps_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload or {})
    merged = dict(payload)

    coords = payload.get("coords")
    if isinstance(coords, dict):
        for k, v in coords.items():
            if v is not None and merged.get(k) is None:
                merged[k] = v

    gps = payload.get("gps")
    if isinstance(gps, dict):
        nested_curr = gps.get("current")
        if isinstance(nested_curr, dict):
            for k, v in nested_curr.items():
                if v is not None and merged.get(k) is None:
                    merged[k] = v
        nested_base = gps.get("base")
        if isinstance(nested_base, dict):
            for k, v in nested_base.items():
                if v is not None and merged.get(f"base_{k}") is None:
                    merged[f"base_{k}"] = v
        for k, v in gps.items():
            if v is not None and merged.get(k) is None:
                merged[k] = v

    if "current_latitude" in merged and merged.get("latitude") is None:
        merged["latitude"] = merged.get("current_latitude")
    if "current_longitude" in merged and merged.get("longitude") is None:
        merged["longitude"] = merged.get("current_longitude")
    if "current_accuracy_m" in merged and merged.get("accuracy") is None:
        merged["accuracy"] = merged.get("current_accuracy_m")
    if "current_accuracy" in merged and merged.get("accuracy") is None:
        merged["accuracy"] = merged.get("current_accuracy")

    return merged


def start_field_session(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    global _LATEST_SESSION_ID
    idempotency_key = str(payload.get("idempotency_key") or "").strip()
    if idempotency_key and idempotency_key in _START_IDEMPOTENCY:
        session = _SESSIONS.get(_START_IDEMPOTENCY[idempotency_key])
        if session:
            return {
                **session_status(session.session_id),
                **_session_start_contract(session.session_id),
                "status": "FIELD_SESSION_STARTED",
                "idempotent_replay": True,
            }
    # Resolve centralized model status (never returns UNKNOWN)
    vision_status = resolve_vision_runtime_status()
    runtime_model_status = vision_status.get("runtime_model_status", "MODEL_NOT_READY")
    tree_model_status_value = vision_status.get("tree_model_status", "MODEL_NOT_READY")
    reason_codes = list(vision_status.get("reason_codes", []))
    reason_codes.extend(["FOREGROUND_RECORDING_REQUIRED", "BROWSER_GEOLOCATION_NATIVE_HIGH_ACCURACY_REQUESTED"])

    session_id = str(payload.get("session_id") or f"FS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    base = _select_base_gps(payload)
    current = _select_current_gps(payload)
    if not _gps_has_coordinates(current):
        current = base

    session = FieldSession(
        session_id=session_id,
        point_id=str(payload.get("point_id") or "V001_pohon_sono"),
        operator_name=str(payload.get("operator_name") or ""),
        started_at=datetime.now().isoformat(),
        session_status="RECORDING_ACTIVE",
        secure_context_status=str(payload.get("secure_context_status") or "SECURE_CONTEXT_UNKNOWN"),
        public_tunnel_status=str(payload.get("public_tunnel_status") or "PUBLIC_TUNNEL_NOT_RUNNING"),
        base_gps=base,
        current_gps=current,
        gps_history=[base] if base.get("latitude") is not None and base.get("longitude") is not None else [],
        camera_status=str(payload.get("camera_status") or "CAMERA_WAITING_PERMISSION"),
        model_status=runtime_model_status,
        latest_result=_base_result(runtime_model_status),
        start_idempotency_key=idempotency_key,
        source_mode=_source_mode(payload, session_id=session_id),
        reason_codes=reason_codes,
    )
    _apply_visibility_payload(session, payload)
    _SESSIONS[session_id] = session
    _LATEST_SESSION_ID = session_id
    if idempotency_key:
        _START_IDEMPOTENCY[idempotency_key] = session_id
    _save_session(session, runtime_root=runtime_root)

    # Build response with resolver results
    response = {**session_status(session_id), **_session_start_contract(session_id), "status": "FIELD_SESSION_STARTED"}
    # Ensure resolver values are in response
    response.update({
        "tree_model_status": tree_model_status_value,
        "runtime_model_status": runtime_model_status,
        "no_fake_detection": vision_status.get("no_fake_detection", True),
        "reason_codes": _dedupe(reason_codes),
    })
    return response


def stop_field_session(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    session = _resolve_session_for_stop(payload.get("session_id"))
    if session is None:
        return {
            "status": "NO_ACTIVE_SESSION_TO_STOP",
            "recording_status": "RECORDING_ACTIVE",
            "session_status": "RECORDING_STOPPED",
            "no_fake_detection": True,
            "no_fake_gps": True,
        }
    _apply_visibility_payload(session, payload)
    session.session_status = "RECORDING_STOPPED"
    session.stopped_at = datetime.now().isoformat()
    if "FOREGROUND_RECORDING_REQUIRED" not in session.reason_codes:
        session.reason_codes.append("FOREGROUND_RECORDING_REQUIRED")
    _save_session(session, runtime_root=runtime_root)
    return {**session_status(session.session_id), "status": "FIELD_SESSION_STOPPED"}


def update_field_session_gps(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    session = _resolve_existing_session(payload.get("session_id"), runtime_root=runtime_root)
    if session is None:
        return {
            "status": "FIELD_SESSION_ID_REQUIRED" if not str(payload.get("session_id") or "").strip() else "FIELD_SESSION_NOT_FOUND",
            "session_id": str(payload.get("session_id") or ""),
            "http_status": 400 if not str(payload.get("session_id") or "").strip() else 404,
            "ok": False,
            "gps_status": "GPS_NOT_READY",
            "no_fake_gps": True,
            "no_fake_detection": True,
        }
    _apply_visibility_payload(session, payload)
    gps = normalize_gps(payload)
    if not session.base_gps or payload.get("set_base"):
        session.base_gps = gps
    session.current_gps = gps
    session.gps_history.append(gps)
    derived = distance_reliability(session.base_gps, session.current_gps)
    session.latest_result = {**session.latest_result, **derived}
    if derived["gps_accuracy_status"] == "GPS_ACCURACY_LOW":
        _add_reason(session, "GPS_ACCURACY_LOW")
    for reason in gps.get("gps_quality_reasons", []):
        _add_reason(session, str(reason))
    if not derived["is_distance_reliable"]:
        _add_reason(session, str(derived["distance_reliability_status"]))
    _save_session(session, runtime_root=runtime_root)
    status = "GPS_UPDATED"
    gps_status = "GPS_ACTIVE"
    if not _gps_has_coordinates(gps):
        status = "GPS_INVALID_SAFE"
        gps_status = "GPS_NOT_READY"
    elif not derived.get("is_distance_reliable"):
        status = str(derived.get("distance_reliability_status") or "GPS_UPDATED")
    return {
        "ok": True,
        "status": status,
        "legacy_status": "FIELD_SESSION_GPS_UPDATED",
        "session_id": session.session_id,
        "gps_status": gps_status,
        "gps_source": gps.get("source", "GPS_SOURCE_BROWSER"),
        "latitude": gps.get("latitude"),
        "longitude": gps.get("longitude"),
        "accuracy_m": gps.get("accuracy"),
        "gps": gps,
        "derived_gps": derived,
        "no_fake_gps": True,
        "no_fake_detection": True,
    }


def process_field_session_frame(payload: dict[str, Any], *, runtime_root: Path) -> dict[str, Any]:
    key = str(payload.get("session_id") or "").strip()
    if not key:
        return {
            "status": "FIELD_SESSION_ID_REQUIRED",
            "error_code": "FIELD_SESSION_ID_REQUIRED",
            "http_status": 400,
            "detections": [],
            "detected_classes": [],
            "no_fake_detection": True,
            "no_fake_gps": True,
        }
    session = _resolve_existing_session(key, runtime_root=runtime_root)
    if session is None:
        return {
            "status": "FIELD_SESSION_NOT_FOUND",
            "session_id": key,
            "http_status": 404,
            "detections": [],
            "detected_classes": [],
            "no_fake_detection": True,
            "no_fake_gps": True,
        }

    # Get centralized vision runtime status (never returns UNKNOWN)
    vision_status = resolve_vision_runtime_status()
    runtime_model_status = vision_status.get("runtime_model_status", "MODEL_NOT_READY")
    tree_model_status_value = vision_status.get("tree_model_status", "MODEL_NOT_READY")
    reason_codes = list(vision_status.get("reason_codes", []))

    # If model not ready, return early without processing frame
    if runtime_model_status != "YOLO_LOCAL_READY":
        return {
            "status": "MODEL_NOT_READY",
            "session_id": key,
            "runtime_model_status": runtime_model_status,
            "tree_model_status": tree_model_status_value,
            "detections": [],
            "detected_classes": [],
            "model_status": runtime_model_status,
            "no_fake_detection": True,
            "no_fake_gps": True,
            "reason_codes": reason_codes,
        }

    _apply_visibility_payload(session, payload)
    _apply_payload_gps_to_session(session, payload)
    decode = decode_frame_image_bytes(payload)
    if decode["status"] in {"FRAME_SKIPPED_NO_IMAGE", "FRAME_DECODE_FAILED_SAFE", "FRAME_TOO_LARGE_DROPPED_SAFE"}:
        result = _safe_frame_result(session, status=decode["status"], extra=decode)
        session.latest_frame_status = result
        session.latest_measurement = result.get("measurement_result", {})
        session.latest_result = build_latest_result(session.session_id, frame_result=result)
        _save_session(session, runtime_root=runtime_root)
        # Merge resolver results
        result.update({
            "runtime_model_status": runtime_model_status,
            "tree_model_status": tree_model_status_value,
            "no_fake_detection": vision_status.get("no_fake_detection", True),
            "reason_codes": _dedupe(list(set(reason_codes) | set(result.get("reason_codes", [])))),
        })
        return result
    pipeline = process_realtime_yolo_frame(payload)
    result = _session_frame_result_from_tree(session, pipeline)
    result = apply_stability_filter(session.session_id, result)
    session.latest_frame_status = result
    session.latest_measurement = result.get("measurement_result", {})
    session.model_status = result.get("model_status", session.model_status)
    session.latest_result = build_latest_result(session.session_id, frame_result=result)
    _save_session(session, runtime_root=runtime_root)

    # Ensure resolver values are in response
    result.update({
        "runtime_model_status": runtime_model_status,
        "tree_model_status": tree_model_status_value,
        "no_fake_detection": vision_status.get("no_fake_detection", True),
        "reason_codes": _dedupe(list(set(reason_codes) | set(result.get("reason_codes", [])))),
    })
    return {**result, "session_id": session.session_id, "session_status": session.session_status}


def shutter_field_session(payload: dict[str, Any], *, runtime_root: Path) -> dict[str, Any]:
    if not str(payload.get("session_id") or "").strip() and _source_mode(payload, session_id="") == "LIVE_OPERATOR":
        return {
            "ok": False,
            "status": "FIELD_SESSION_ID_REQUIRED",
            "error_code": "FIELD_SESSION_ID_REQUIRED",
            "http_status": 400,
            "csv_appended": False,
            "duplicate_ignored": False,
            "map_enabled": False,
            "result_enabled": False,
            "no_fake_detection": True,
            "no_fake_gps": True,
        }

    # Get centralized vision runtime status
    vision_status = resolve_vision_runtime_status()
    runtime_model_status = vision_status.get("runtime_model_status", "MODEL_NOT_READY")
    tree_model_status_value = vision_status.get("tree_model_status", "MODEL_NOT_READY")
    reason_codes = list(vision_status.get("reason_codes", []))

    session = _resolve_session_for_shutter(payload, runtime_root=runtime_root)
    payload = dict(payload)
    _apply_visibility_payload(session, payload)
    _apply_payload_gps_to_session(session, payload)
    payload.setdefault("image_jpeg_base64", payload.get("image_base64") or payload.get("frame_image_base64"))
    payload.setdefault("frame_jpeg_base64", payload.get("image_base64") or payload.get("frame_image_base64"))
    payload.setdefault("point_id", session.point_id)
    payload.setdefault("operator_name", session.operator_name)
    payload.setdefault("model_status", session.model_status)
    payload.setdefault("gps_lat", session.current_gps.get("latitude"))
    payload.setdefault("gps_lon", session.current_gps.get("longitude"))
    payload.setdefault("gps_accuracy_m", session.current_gps.get("accuracy"))
    payload.setdefault("gps_source", session.current_gps.get("source", "GPS_SOURCE_BROWSER"))
    payload.setdefault("latest_measurement", session.latest_measurement)
    duplicate = _duplicate_shutter_result(session, payload)
    if duplicate:
        return duplicate
    session.capture_sequence += 1
    report_id = f"CAP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_short_session(session.session_id)}_{session.capture_sequence:04d}"
    snapshot = _write_session_shutter_image(payload, runtime_root=runtime_root, report_id=report_id)
    map_result = latest_field_session_map(session.session_id, runtime_root=runtime_root)
    row = _build_session_report_row(session, payload, report_id=report_id, snapshot_path=snapshot.get("snapshot_path", ""), map_result=map_result)
    csv_result = append_session_report_row(session, {"row": row, "page_source": "field_session_shutter"})

    # Determine if GPS valid for map
    current_truth = validate_gps_evidence(session.current_gps)
    map_enabled = current_truth.get("marker_allowed", False)
    detection_count = len(session.latest_measurement.get("detected_classes", []))

    session.latest_report = {
        "status": "FIELD_SESSION_SHUTTER_SAVED",
        "legacy_status": "FIELD_SESSION_REPORT_WRITTEN",
        "report_id": report_id,
        "csv_appended": True,
        "duplicate_ignored": False,
        "idempotency_key": row.get("idempotency_key"),
        "capture_sequence": session.capture_sequence,
        "snapshot_status": snapshot.get("status"),
        "snapshot_path": snapshot.get("snapshot_path"),
        "report_csv_path": csv_result["csv_path"],
        "report_csv_url": f"/field-reports/{Path(csv_result['csv_path']).name}",
        "google_sheets_status": "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY",
        "map_status": map_result.get("status"),
        "map_path": map_result.get("path"),
        "map_url": f"/field-map/session/{session.session_id}",
        "map_html_url": map_result.get("map_url"),
        "spreadsheet_url": f"/field-spreadsheet/session/{session.session_id}",
        "result_url": f"/field-spreadsheet/session/{session.session_id}",
        "result_status": "SPREADSHEET_READY",
        "shutter_done": True,
        "evidence_created": True,
        "map_enabled": map_enabled,
        "result_enabled": True,
        "ok": True,
        "runtime_model_status": runtime_model_status,
        "tree_model_status": tree_model_status_value,
        "detection_count": detection_count,
        "no_fake_detection": vision_status.get("no_fake_detection", True),
        "no_fake_gps": True,
        **_session_row_fields(session, page_source="field_session_shutter"),
        "result_page_url": f"/field-spreadsheet/session/{session.session_id}",
        "report_page_url": f"/field-report?session_id={session.session_id}",
        "row": row,
        "reason_codes": _dedupe(reason_codes),
    }
    _remember_shutter(session, payload, session.latest_report)
    _save_session(session, runtime_root=runtime_root)
    return session.latest_report


def record_manual_input(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    global _LATEST_MANUAL_INPUT
    session = _get_or_latest(payload.get("session_id"), create_if_missing=True)
    _apply_visibility_payload(session, payload)
    result = {
        "status": "MANUAL_OPERATOR_INPUT_NOT_AI_DETECTION",
        "manual_input_status": "MANUAL_OPERATOR_INPUT_NOT_AI_DETECTION",
        "session_id": session.session_id,
        "point_id": payload.get("point_id") or session.point_id,
        "object_type": payload.get("object_type") or "pohon_sono",
        "estimated_distance_m": _to_float(payload.get("estimated_distance_m")),
        "estimated_tree_height_m": _to_float(payload.get("estimated_tree_height_m")),
        "estimated_conductor_height_m": _to_float(payload.get("estimated_conductor_height_m")),
        "obstruction_reason": payload.get("obstruction_reason") or "",
        "operator_notes": payload.get("operator_notes") or payload.get("notes") or "",
        "gps": session.current_gps,
        "no_fake_detection": True,
    }
    session.latest_result = {**session.latest_result, **result}
    _LATEST_MANUAL_INPUT = result
    _save_session(session, runtime_root=runtime_root)
    return result


def session_status(session_id: Any | None = None) -> dict[str, Any]:
    session = _get_or_latest(session_id, create_if_missing=True)
    derived = distance_reliability(session.base_gps, session.current_gps)
    gps_truth = validate_gps_evidence(session.current_gps)
    readiness = model_readiness_status()
    return {
        "status": "FIELD_SESSION_STATUS_READY",
        "session": asdict(session),
        "session_id": session.session_id,
        "session_status": session.session_status,
        "recording_status": session.session_status,
        "foreground_recording_status": session.foreground_recording_status,
        "visibility_state": session.visibility_state,
        "hidden_started_at": session.hidden_started_at,
        "hidden_duration_ms": session.hidden_duration_ms,
        "frame_loop_paused_due_to_hidden": session.frame_loop_paused_due_to_hidden,
        "browser_throttle_warning": session.browser_throttle_warning,
        "gps": {"base": session.base_gps, "current": session.current_gps, "history_count": len(session.gps_history)},
        "derived_gps": derived,
        "gps_status": derived.get("gps_accuracy_status"),
        "gps_precision_status": gps_truth["gps_precision_status"],
        "gps_marker_status": gps_truth["status"],
        "gps_quality_reasons": gps_truth["gps_quality_reasons"],
        "camera_status": session.camera_status,
        "model_status": session.model_status,
        "tree_model_status": readiness.get("tree_model_status"),
        "multiclass_model_status": "MULTICLASS_MODEL_READY_CANDIDATE" if readiness.get("status") == "MULTICLASS_MODEL_READY_CANDIDATE" else "MULTICLASS_MODEL_NOT_READY",
        "pole_model_status": readiness.get("pole_model_status", "POLE_MODEL_NOT_READY"),
        "conductor_model_status": readiness.get("conductor_model_status", "CONDUCTOR_MODEL_NOT_READY"),
        "geometry_status": readiness.get("geometry_readiness", "AUTO_GEOMETRY_BLOCKED_WAITING_FOR_POLE_CONDUCTOR_MODEL"),
        "clearance_status": "CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR",
        "no_fake_gps": True,
        "no_fake_detection": True,
    }


def build_latest_result(session_id: Any | None = None, *, frame_result: dict[str, Any] | None = None) -> dict[str, Any]:
    session = _get_or_latest(session_id, create_if_missing=True)
    frame_result = frame_result or session.latest_frame_status or {}
    measurement = frame_result.get("measurement_result") or session.latest_measurement or {}
    derived = distance_reliability(session.base_gps, session.current_gps)
    model_status = frame_result.get("model_status") or session.model_status or "MODEL_NOT_READY"
    status = "FIELD_RESULT_PROVISIONAL"
    result_status = "FIELD_RESULT_PROVISIONAL"
    reason_codes = list(session.reason_codes)
    if model_status == "MODEL_NOT_READY":
        status = "MODEL_NOT_READY_NO_FAKE_DETECTION"
        result_status = "MODEL_NOT_READY_NO_AI_DETECTION"
        reason_codes.append("MODEL_NOT_READY_NO_FAKE_DETECTION")
    if not measurement.get("clearance_m"):
        reason_codes.append("INSUFFICIENT_GEOMETRY_DATA")
    if derived.get("gps_accuracy_status") == "GPS_ACCURACY_LOW" or not derived.get("is_distance_reliable"):
        reason_codes.append("GPS_LOW_ACCURACY_DISTANCE_NOT_RELIABLE")
    if measurement.get("calibration_status", "CALIBRATION_NOT_READY") != "CALIBRATION_READY":
        reason_codes.append("CALIBRATION_NOT_READY_CLEARANCE_NOT_FINAL")
    zone_status = measurement.get("zone_status") if measurement.get("clearance_m") is not None else "INSUFFICIENT_DATA"
    action_recommendation = measurement.get("action_recommendation")
    if model_status == "MODEL_NOT_READY":
        action_recommendation = "Lanjutkan labeling/training custom model; jangan jadikan hasil ini klaim deteksi."
    elif zone_status == "INSUFFICIENT_DATA":
        action_recommendation = "Lengkapi model, kalibrasi, dan evidence lapangan sebelum keputusan pemangkasan."
    result = {
        "status": status,
        "result_status": result_status,
        "session_id": session.session_id,
        "model_status": model_status,
        "geometry_status": "INSUFFICIENT_GEOMETRY_DATA" if not measurement.get("clearance_m") else "GEOMETRY_PROVISIONAL",
        "gps_quality_status": derived["gps_accuracy_status"],
        "risk_zone": zone_status,
        "zone_status": zone_status,
        "clearance_m": measurement.get("clearance_m"),
        "confidence_status": measurement.get("confidence_status", "CALIBRATION_NOT_READY"),
        "measurement_quality_label": measurement.get("measurement_quality_label", "INSUFFICIENT_GEOMETRY_DATA"),
        "eta_days": measurement.get("eta_days"),
        "action_recommendation": action_recommendation,
        "field_result_disclaimer": "FIELD_RESULT_PROVISIONAL",
        "reason_codes": _dedupe(reason_codes),
        **derived,
        "no_fake_gps": True,
        "no_fake_detection": True,
    }
    result["growth_prior"] = predict_growth_prior(
        {
            "point_id": session.point_id,
            "species": "pohon_sono",
            "clearance_m": measurement.get("clearance_m"),
        }
    )
    session.latest_result = result
    return result


def latest_field_session_report(session_id: Any | None = None) -> dict[str, Any]:
    if session_id:
        _load_session_from_disk(str(session_id))
    session = _get_or_latest(session_id, create_if_missing=True)
    if session.latest_report:
        return session.latest_report
    return {
        "status": "NO_FIELD_SESSION_REPORT_YET",
        "session_id": session.session_id,
        "report_csv_path": str(PROGRESS5_4_REPORT_CSV),
        "report_csv_url": f"/field-reports/{PROGRESS5_4_REPORT_CSV.name}",
        "result_page_url": f"/field-result?session_id={session.session_id}",
        "report_page_url": f"/field-report?session_id={session.session_id}",
        "map_url": f"/field-map/session/{session.session_id}",
    }


def field_session_spreadsheet(session_id: Any | None, *, runtime_root: Path | None = None) -> dict[str, Any]:
    key = str(session_id or "").strip()
    if not key:
        return {
            "status": "RESULT_SESSION_ID_REQUIRED",
            "session_id": "",
            "spreadsheet_status": "RESULT_REQUIRES_SHUTTER",
            "google_sheets_status": "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_SPREADSHEET_READY",
            "rows": [],
        }
    session = _resolve_existing_session(key, runtime_root=runtime_root)
    if session is None:
        return {
            "status": "RESULT_SESSION_NOT_FOUND",
            "session_id": key,
            "spreadsheet_status": "RESULT_SESSION_NOT_FOUND",
            "google_sheets_status": "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_SPREADSHEET_READY",
            "rows": [],
        }
    if not session.latest_report:
        return {
            "status": "RESULT_REQUIRES_SHUTTER",
            "session_id": session.session_id,
            "spreadsheet_status": "RESULT_REQUIRES_SHUTTER",
            "google_sheets_status": "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_SPREADSHEET_READY",
            "rows": [],
            "message": "Jepret dulu untuk membuat spreadsheet evidence.",
        }
    row = dict(session.latest_report.get("row") or {})
    growth = predict_growth_prior({"point_id": session.point_id, "species": "pohon_sono", "clearance_m": row.get("clearance_m")})
    row.update(
        {
            "session_id": session.session_id,
            "tree_confidence": row.get("tree_confidence") or session.latest_frame_status.get("tree_confidence", ""),
            "tree_bbox": row.get("tree_bbox") or json.dumps(session.latest_frame_status.get("tree_bbox_xyxy") or "", ensure_ascii=False),
            "pole_detected": False,
            "conductor_detected": False,
            "growth_prior_status": growth.get("growth_prior_status"),
            "growth_model_status": growth.get("growth_model_status"),
            "growth_selected_model": growth.get("selected_model_name"),
            "growth_validation_mae": growth.get("validation_mae"),
            "growth_validation_rmse": growth.get("validation_rmse"),
            "growth_validation_r2": growth.get("validation_r2"),
            "growth_year_m": growth.get("estimated_height_growth_m_per_year"),
            "eta_3m_status": growth.get("eta_3m_status") or growth.get("eta_to_3m_clearance_days"),
            "source_status": "PROXY_NOT_FIELD_OBSERVED",
            "map_url": f"/field-map/session/{session.session_id}",
            "frame_status": session.latest_frame_status.get("status", "FRAME_NOT_AVAILABLE"),
        }
    )
    ordered = _spreadsheet_row(row)
    return {
        "status": "RESULT_SPREADSHEET_READY",
        "spreadsheet_status": "RESULT_SPREADSHEET_READY",
        "session_id": session.session_id,
        "google_sheets_status": "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_SPREADSHEET_READY",
        "csv_url": session.latest_report.get("report_csv_url") or f"/field-reports/{_session_report_csv(session).name}",
        "map_url": f"/field-map/session/{session.session_id}",
        "rows": [ordered],
        "columns": list(ordered.keys()),
        "no_fake_detection": True,
        "no_fake_gps": True,
    }


def render_field_session_spreadsheet_html(session_id: Any | None, *, runtime_root: Path | None = None) -> str:
    result = field_session_spreadsheet(session_id, runtime_root=runtime_root)
    session_id_text = html.escape(str(result.get("session_id") or session_id or ""))
    rows = result.get("rows") or []

    if not rows:
        content = f"""
        <div class="card">
          <p>{html.escape(str(result.get('message') or result.get('status')))}</p>
          <a class="btn" href="/field-camera?session_id={session_id_text}">Back to Camera</a>
        </div>
        """
    else:
        # Build cards first
        r = rows[0]
        content = f"""
        <div class="cards-grid">
            <div class="evidence-card"><b>Session ID:</b><br>{html.escape(str(r.get('session_id', '')))}</div>
            <div class="evidence-card"><b>Point ID:</b><br>{html.escape(str(r.get('point_id', '')))}</div>
            <div class="evidence-card"><b>Operator:</b><br>{html.escape(str(r.get('operator_name', '')))}</div>
            <div class="evidence-card"><b>Timestamp:</b><br>{html.escape(str(r.get('timestamp', '')))}</div>
            <div class="evidence-card"><b>Frame Status:</b><br>{html.escape(str(r.get('frame_status', '')))}</div>
            <div class="evidence-card"><b>GPS Coordinate:</b><br>{html.escape(str(r.get('gps_lat', '')))}, {html.escape(str(r.get('gps_lon', '')))}</div>
            <div class="evidence-card"><b>GPS Accuracy:</b><br>{html.escape(str(r.get('gps_accuracy_m', '')))} m</div>
            <div class="evidence-card"><b>Tree Model Status:</b><br>{html.escape(str(result.get('tree_model_status', 'TREE_MODEL_READY_CANDIDATE')))}</div>
            <div class="evidence-card"><b>Pole Model Status:</b><br>{html.escape(str(r.get('pole_model_status', 'POLE_MODEL_NOT_READY')))}</div>
            <div class="evidence-card"><b>Conductor Model:</b><br>{html.escape(str(r.get('conductor_model_status', 'CONDUCTOR_MODEL_NOT_READY')))}</div>
            <div class="evidence-card"><b>Clearance Status:</b><br>CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR</div>
            <div class="evidence-card"><b>ETA Status:</b><br>{html.escape(str(r.get('eta_3m_status', 'ETA_3M_NOT_AVAILABLE_INSUFFICIENT_GEOMETRY')))}</div>
            <div class="evidence-card"><b>Growth Selected Model:</b><br>{html.escape(str(r.get('growth_selected_model', '')))}</div>
            <div class="evidence-card"><b>CSV Mode:</b><br>{html.escape(str(result.get('google_sheets_status')))}</div>
        </div>
        """

        header = "".join(f"<th>{html.escape(str(column))}</th>" for column in result["columns"])
        body = "".join(f"<td>{html.escape(str(r.get(column, '')))}</td>" for column in result["columns"])
        table = f"<div class=\"sheet-wrap\"><table><thead><tr>{header}</tr></thead><tbody><tr>{body}</tr></tbody></table></div>"

        content += f"""
        <div class="card table-container">
            <h3>Tabel Detail</h3>
            {table}
        </div>
        <p>
            <a class="btn" href="/field-camera?session_id={session_id_text}">Kembali ke Camera</a>
            <a class="btn" href="/field-map/session/{session_id_text}">Map</a>
        </p>
        <p>
            <a class="btn" href="{html.escape(str(result.get('csv_url') or ''))}">Download CSV</a>
        </p>
        """

    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Spreadsheet Evidence</title>
<style>
body{{margin:0;font-family:system-ui;background:#eef6f4;color:#102024}}
.wrap{{max-width:1100px;margin:0 auto;padding:22px}}
.card{{background:white;border-radius:24px;padding:18px;box-shadow:0 14px 40px rgba(0,0,0,.08);overflow:auto;margin-bottom:20px;}}
.cards-grid{{display:grid;grid-template-columns:repeat(auto-fill, minmax(200px, 1fr));gap:12px;margin-bottom:20px;}}
.evidence-card{{background:white;border:1px solid #d6e2df;border-radius:16px;padding:12px;box-shadow:0 4px 12px rgba(0,0,0,.04);font-size:13px;}}
table{{border-collapse:collapse;width:100%;font-size:14px;min-width:900px;}}
td,th{{border:1px solid #d6e2df;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}
th{{background:#166b5a;color:white;position:sticky;top:0;}}
.btn{{display:inline-block;margin:10px 8px 10px 0;padding:12px 16px;border-radius:14px;background:#166b5a;color:white;text-decoration:none;font-weight:800}}
.table-container{{max-height: 50vh;}}
</style>
</head>
<body>
<div class="wrap">
    <h1>Spreadsheet Evidence</h1>
    {content}
</div>
</body>
</html>"""


def latest_field_session_map(session_id: Any | None = None, *, runtime_root: Path | None = None, require_shutter: bool = False) -> dict[str, Any]:
    key = str(session_id or "").strip()
    if key:
        session = _resolve_existing_session(key, runtime_root=runtime_root)
        if session is None:
            if key.startswith("P65_") and not require_shutter:
                return {
                    "status": "NO_GPS_NO_MARKER",
                    "session_id": key,
                    "map_status": "NO_GPS_NO_MARKER",
                    "map_exists": False,
                    "message": "GPS belum valid, marker tidak dibuat.",
                    "gps_precision_status": "INVALID_COORDINATE_NULL",
                    "gps_quality_reasons": ["INVALID_COORDINATE_NULL", "GPS_ACCURACY_NOT_PROVIDED"],
                }
            return {
                "status": "FIELD_SESSION_NOT_FOUND",
                "session_id": key,
                "map_status": "FIELD_SESSION_NOT_FOUND",
                "map_exists": False,
                "message": "Session tidak ditemukan. Mulai ulang dari halaman Capture.",
            }
    elif not _LATEST_SESSION_ID:
        return {
            "status": "NO_GPS_NO_MARKER",
            "session_id": "",
            "map_status": "NO_FIELD_SESSION_YET",
            "map_exists": False,
            "message": "Belum ada session field aktif.",
        }
    else:
        session = _get_or_latest(None, create_if_missing=False)
    if require_shutter and session.source_mode == "LIVE_OPERATOR" and session.capture_sequence <= 0 and not session.latest_report:
        return {
            "status": "MAP_LOCKED_SHUTTER_REQUIRED",
            "session_id": session.session_id,
            "map_status": "MAP_LOCKED_SHUTTER_REQUIRED",
            "map_exists": False,
            "field_map_url": f"/field-map/session/{session.session_id}",
            "message": "Jepret dulu untuk membuat evidence map.",
            "no_fake_gps": True,
        }
    current = session.current_gps
    derived = distance_reliability(session.base_gps, session.current_gps)
    base_truth = validate_gps_evidence(session.base_gps)
    current_truth = validate_gps_evidence(current)
    map_path = _session_map_path(session.session_id, runtime_root=runtime_root)
    if not current_truth["marker_allowed"]:
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(_basic_map_html(None, None, session.point_id, session=session, derived=derived, gps_truth=current_truth), encoding="utf-8")
        return {
            "status": "NO_GPS_NO_MARKER",
            "session_id": session.session_id,
            "path": str(map_path),
            "map_url": f"/field-maps/{map_path.name}",
            "field_map_url": f"/field-map/session/{session.session_id}",
            "map_exists": True,
            "message": "GPS belum valid, marker tidak dibuat.",
            "gps_precision_status": current_truth["gps_precision_status"],
            "gps_quality_reasons": current_truth["gps_quality_reasons"],
        }
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(
        _basic_map_html(current.get("latitude"), current.get("longitude"), session.point_id, session=session, derived=derived, gps_truth=current_truth, base_truth=base_truth),
        encoding="utf-8",
    )
    return {
        "status": "MAP_HTML_READY",
        "google_maps_status": "GOOGLE_MAPS_NOT_CONFIGURED",
        "session_id": session.session_id,
        "path": str(map_path),
        "map_url": f"/field-maps/{map_path.name}",
        "field_map_url": f"/field-map/session/{session.session_id}",
        "map_exists": True,
        "base_marker_status": base_truth["status"],
        "current_marker_status": current_truth["status"],
        "gps_precision_status": current_truth["gps_precision_status"],
        "gps_quality_reasons": current_truth["gps_quality_reasons"],
    }


def render_field_session_map_html(session_id: Any | None, *, runtime_root: Path | None = None) -> str:
    result = latest_field_session_map(session_id, runtime_root=runtime_root, require_shutter=True)
    path_text = str(result.get("path") or "").strip()
    path = Path(path_text) if path_text else Path("__missing_field_map__")
    if path_text and path.is_file():
        return path.read_text(encoding="utf-8")

    session_id_text = html.escape(str(result.get("session_id") or session_id or ""))
    status = html.escape(str(result.get("status") or "FIELD_SESSION_MAP_STATUS"))
    message = html.escape(str(result.get("message") or "Map belum tersedia."))

    if status == "MAP_LOCKED_SHUTTER_REQUIRED":
        content = f"""
        <div class="card warn">
          <h2>MAP_LOCKED_SHUTTER_REQUIRED</h2>
          <p>{message}</p>
          <a class="btn" href="/field-camera?session_id={session_id_text}">Back to Camera</a>
        </div>
        """
    else:
        content = f"""
        <div class="card warn">
          <h2>NO_GPS_NO_MARKER</h2>
          <p>GPS belum valid, marker tidak dibuat. Data tetap disimpan sebagai evidence non-spasial.</p>
          <p><b>Reasons:</b> {html.escape(str(result.get('gps_quality_reasons', [])))}</p>
          <p>
            <a class="btn" href="/field-camera?session_id={session_id_text}">Back to Camera</a>
            <a class="btn" href="/field-spreadsheet/session/{session_id_text}">Result</a>
          </p>
        </div>
        """

    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Field Map {session_id_text}</title>
<style>
body{{margin:0;font-family:system-ui;background:linear-gradient(135deg,#e8f4ef,#f8fbff);color:#102024}}
.wrap{{max-width:900px;margin:0 auto;padding:24px}}
.card{{background:rgba(255,255,255,.84);border:1px solid rgba(0,0,0,.08);border-radius:28px;padding:22px;box-shadow:0 18px 50px rgba(0,0,0,.08)}}
.ok{{border-left:8px solid #166b5a}}
.warn{{border-left:8px solid #b7791f}}
.btn{{display:inline-block;margin-top:14px;margin-right:8px;padding:14px 18px;border-radius:16px;background:#166b5a;color:white;text-decoration:none;font-weight:800}}
small{{overflow-wrap:anywhere}}
</style>
</head>
<body>
<div class="wrap">
<h1>Map Evidence</h1>
<p><small>Session: {session_id_text}</small></p>
{content}
</div>
</body>
</html>"""


def validate_conductor_height(conductor_height_m: Any) -> dict[str, Any]:
    height = _to_float(conductor_height_m)
    if height is None:
        return {"status": "CONDUCTOR_HEIGHT_NOT_PROVIDED", "conductor_height_m": None}
    if height < 1.0 or height > 12.0:
        return {"status": "CONDUCTOR_HEIGHT_OUT_OF_CONFIG_RANGE", "conductor_height_m": height}
    return {"status": "CONDUCTOR_HEIGHT_IN_CONFIG_RANGE", "conductor_height_m": height}


def classify_clearance(tree_height_m: Any, conductor_height_m: Any = 11.0) -> dict[str, Any]:
    conductor = validate_conductor_height(conductor_height_m)
    tree = _to_float(tree_height_m)
    if conductor["status"] != "CONDUCTOR_HEIGHT_IN_CONFIG_RANGE":
        return {**conductor, "clearance_m": None, "zone_status": "INSUFFICIENT_DATA"}
    if tree is None:
        return {**conductor, "clearance_m": None, "zone_status": "INSUFFICIENT_DATA"}
    clearance = round(conductor["conductor_height_m"] - tree, 3)
    if clearance <= 3.0:
        zone = "TEBANG"
    elif clearance <= 4.0:
        zone = "PANTAUAN"
    else:
        zone = "AMAN"
    return {**conductor, "tree_height_m": tree, "clearance_m": clearance, "zone_status": zone}


def append_session_report_row(session: FieldSession, report: dict[str, Any]) -> dict[str, Any]:
    csv_path = _session_report_csv(session)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    _ensure_report_schema(csv_path)
    write_header = not csv_path.exists()
    row = {key: "" for key in PROGRESS5_4_REPORT_COLUMNS}
    row.update(report.get("row") or {})
    row.update(_session_row_fields(session, page_source=report.get("page_source") or "field_session"))
    row["csv_path"] = str(csv_path)
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROGRESS5_4_REPORT_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in PROGRESS5_4_REPORT_COLUMNS})
    return {"status": "SESSION_REPORT_ROW_APPENDED", "csv_path": str(csv_path), "source_mode": session.source_mode}


def _session_row_fields(session: FieldSession, *, page_source: str) -> dict[str, Any]:
    derived = distance_reliability(session.base_gps, session.current_gps)
    base_truth = validate_gps_evidence(session.base_gps)
    current_truth = validate_gps_evidence(session.current_gps)
    return {
        "session_id": session.session_id,
        "recording_status": session.session_status,
        "base_latitude": format_coordinate_raw(session.base_gps.get("latitude")),
        "base_longitude": format_coordinate_raw(session.base_gps.get("longitude")),
        "base_accuracy_m": session.base_gps.get("accuracy"),
        "current_latitude": format_coordinate_raw(session.current_gps.get("latitude")),
        "current_longitude": format_coordinate_raw(session.current_gps.get("longitude")),
        "current_accuracy_m": session.current_gps.get("accuracy"),
        "horizontal_distance_from_tree_m": derived.get("horizontal_distance_from_tree_m"),
        "distance_reliability_status": derived.get("distance_reliability_status"),
        "gps_accuracy_status": derived.get("gps_accuracy_status"),
        "gps_quality_reason": derived.get("gps_quality_reason"),
        "foreground_recording_status": session.foreground_recording_status,
        "visibility_state": session.visibility_state,
        "hidden_duration_ms": session.hidden_duration_ms,
        "browser_throttle_warning": session.browser_throttle_warning,
        "manual_input_status": _LATEST_MANUAL_INPUT.get("manual_input_status", ""),
        "page_source": page_source,
        "result_page_url": f"/field-spreadsheet/session/{session.session_id}",
        "report_page_url": f"/field-report?session_id={session.session_id}",
        "spreadsheet_url": f"/field-spreadsheet/session/{session.session_id}",
        "source_mode": session.source_mode,
        "capture_sequence": session.capture_sequence,
        "gps_lat_raw": current_truth["latitude_raw"],
        "gps_lon_raw": current_truth["longitude_raw"],
        "base_latitude_raw": base_truth["latitude_raw"],
        "base_longitude_raw": base_truth["longitude_raw"],
        "current_latitude_raw": current_truth["latitude_raw"],
        "current_longitude_raw": current_truth["longitude_raw"],
        "gps_precision_status": current_truth["gps_precision_status"],
    }


def _build_session_report_row(
    session: FieldSession,
    payload: dict[str, Any],
    *,
    report_id: str,
    snapshot_path: str,
    map_result: dict[str, Any],
) -> dict[str, Any]:
    measurement = payload.get("latest_measurement") if isinstance(payload.get("latest_measurement"), dict) else session.latest_measurement
    measurement = measurement if isinstance(measurement, dict) else {}
    derived = distance_reliability(session.base_gps, session.current_gps)
    current_truth = validate_gps_evidence(session.current_gps)
    growth = predict_growth_prior({"point_id": session.point_id, "species": "pohon_sono", "clearance_m": measurement.get("clearance_m")})
    return {
        "report_id": report_id,
        "timestamp": payload.get("timestamp") or datetime.now().isoformat(),
        "point_id": payload.get("point_id") or session.point_id or "V001_pohon_sono",
        "operator_name": payload.get("operator_name") or session.operator_name,
        "gps_lat": format_coordinate_raw(session.current_gps.get("latitude")) if current_truth["marker_allowed"] else "",
        "gps_lon": format_coordinate_raw(session.current_gps.get("longitude")) if current_truth["marker_allowed"] else "",
        "gps_accuracy_m": session.current_gps.get("accuracy") if session.current_gps.get("accuracy") is not None else "NOT_PROVIDED",
        "gps_source": session.current_gps.get("source") or "GPS_SOURCE_BROWSER",
        "secure_context_status": session.secure_context_status or "NOT_PROVIDED",
        "current_url_mode": payload.get("current_url_mode") or "NOT_PROVIDED",
        "public_tunnel_status": session.public_tunnel_status or "NOT_PROVIDED",
        "model_status": session.model_status or "MODEL_NOT_READY",
        "debug_mode": str(bool(payload.get("debug_mode"))).lower(),
        "detected_classes": ";".join(str(item) for item in measurement.get("detected_classes", [])),
        "pole_detected": measurement.get("pole_detected", False),
        "conductor_detected": measurement.get("conductor_detected", False),
        "tree_detected": measurement.get("tree_detected", False),
        "tree_model_status": session.latest_frame_status.get("tree_model_status") or tree_model_status().get("tree_model_status"),
        "tree_confidence": measurement.get("tree_confidence", session.latest_frame_status.get("tree_confidence", "")),
        "tree_bbox": json.dumps(measurement.get("tree_bbox") or session.latest_frame_status.get("tree_bbox_xyxy") or "", ensure_ascii=False),
        "pole_model_status": "POLE_MODEL_NOT_READY",
        "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
        "pole_reference_height_m": measurement.get("pole_reference_height_m", ""),
        "pole_pixel_height": measurement.get("pole_pixel_height", ""),
        "meter_per_px": measurement.get("meter_per_px", ""),
        "tree_top_px": measurement.get("tree_top_px", ""),
        "cable_px": measurement.get("cable_px", ""),
        "tree_height_m": measurement.get("tree_height_m", ""),
        "cable_height_m": measurement.get("cable_height_m", ""),
        "clearance_m": measurement.get("clearance_m", ""),
        "zone_status": measurement.get("zone_status", "INSUFFICIENT_DATA"),
        "eta_days": measurement.get("eta_days", ""),
        "growth_prior_status": growth.get("growth_prior_status"),
        "growth_model_status": growth.get("growth_model_status"),
        "growth_selected_model": growth.get("selected_model_name"),
        "growth_validation_mae": growth.get("validation_mae"),
        "growth_validation_rmse": growth.get("validation_rmse"),
        "growth_validation_r2": growth.get("validation_r2"),
        "growth_year_m": growth.get("estimated_height_growth_m_per_year"),
        "eta_3m_status": growth.get("eta_3m_status") or growth.get("eta_to_3m_clearance_days"),
        "risk_level": measurement.get("risk_level", "NOT_AVAILABLE"),
        "action_recommendation": measurement.get("action_recommendation", "NOT_AVAILABLE"),
        "latency_ms": payload.get("latency_ms", ""),
        "smoothing_status": measurement.get("smoothing_status", "NOT_AVAILABLE"),
        "calibration_status": measurement.get("calibration_status", "CALIBRATION_NOT_READY"),
        "confidence_status": measurement.get("confidence_status", "MODEL_NOT_READY" if session.model_status == "MODEL_NOT_READY" else "NOT_AVAILABLE"),
        "environment_status": "ENVIRONMENT_NOT_AVAILABLE",
        "notes": payload.get("notes") or payload.get("operator_notes") or "",
        "snapshot_path": snapshot_path,
        "map_status": map_result.get("status", "NO_GPS_NO_MARKER"),
        "reason_codes": ";".join(
            _dedupe(
                [
                    *measurement.get("reason_codes", []),
                    *current_truth.get("gps_quality_reasons", []),
                    str(derived.get("distance_reliability_status") or ""),
                    "MODEL_NOT_READY_NO_FAKE_DETECTION" if session.model_status == "MODEL_NOT_READY" else "",
                ]
            )
        ),
        "idempotency_key": payload.get("idempotency_key") or _shutter_fingerprint(session, payload),
        **_session_row_fields(session, page_source="field_session_shutter"),
    }


def _select_base_gps(payload: dict[str, Any]) -> dict[str, Any]:
    samples = payload.get("gps_samples")
    if isinstance(samples, list):
        normalized = [normalize_gps(sample) for sample in samples if isinstance(sample, dict)]
        best = select_best_gps_sample(normalized)
        if best:
            return best
    return _first_valid_gps_payload(
        _gps_payload(payload, "base"),
        payload.get("base_gps"),
        _nested_gps_payload(payload, "base"),
        payload.get("gps"),
        payload,
    )


def _select_current_gps(payload: dict[str, Any]) -> dict[str, Any]:
    return _first_valid_gps_payload(
        _gps_payload(payload, "current"),
        payload.get("current_gps"),
        _nested_gps_payload(payload, "current"),
        payload.get("gps"),
        payload,
    )


def _gps_payload(payload: dict[str, Any], prefix: str) -> dict[str, Any]:
    nested = payload.get(f"{prefix}_gps")
    if isinstance(nested, dict):
        return nested
    fields = {
        "latitude": payload.get(f"{prefix}_latitude"),
        "longitude": payload.get(f"{prefix}_longitude"),
        "accuracy": payload.get(f"{prefix}_accuracy_m"),
        "altitude": payload.get(f"{prefix}_altitude"),
        "altitudeAccuracy": payload.get(f"{prefix}_altitude_accuracy"),
        "heading": payload.get(f"{prefix}_heading"),
        "speed": payload.get(f"{prefix}_speed"),
        "timestamp": payload.get(f"{prefix}_timestamp") or payload.get("gps_timestamp") or payload.get("timestamp"),
        "source": payload.get("gps_source") or "GPS_SOURCE_BROWSER",
    }
    cleaned = {key: value for key, value in fields.items() if value not in {None, ""}}
    has_coordinate_hint = any(key in cleaned for key in {"latitude", "longitude", "accuracy"})
    return cleaned if has_coordinate_hint else {}


def _nested_gps_payload(payload: dict[str, Any], prefix: str) -> dict[str, Any]:
    gps = payload.get("gps")
    if isinstance(gps, dict) and isinstance(gps.get(prefix), dict):
        return dict(gps[prefix])
    return {}


def _first_valid_gps_payload(*candidates: Any) -> dict[str, Any]:
    fallback: dict[str, Any] | None = None
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        gps = normalize_gps(candidate)
        if _gps_has_coordinates(gps):
            return gps
        if fallback is None and gps.get("accuracy") is not None:
            fallback = gps
    return fallback or normalize_gps({})


def _gps_has_coordinates(gps: dict[str, Any]) -> bool:
    return _to_float(gps.get("latitude")) is not None and _to_float(gps.get("longitude")) is not None


def _apply_payload_gps_to_session(session: FieldSession, payload: dict[str, Any]) -> None:
    base = _select_base_gps(payload)
    current = _select_current_gps(payload)
    if _gps_has_coordinates(base):
        session.base_gps = base
        if not session.gps_history:
            session.gps_history.append(base)
    if _gps_has_coordinates(current):
        session.current_gps = current
        session.gps_history.append(current)
    elif _gps_has_coordinates(base):
        session.current_gps = base


def _resolve_session_for_stop(session_id: Any | None) -> FieldSession | None:
    key = str(session_id or "").strip()
    if key and key in _SESSIONS:
        return _SESSIONS[key]
    active = [session for session in _SESSIONS.values() if session.session_status == "RECORDING_ACTIVE"]
    if active:
        return sorted(active, key=lambda item: item.started_at or "", reverse=True)[0]
    return None


def _resolve_session_for_shutter(payload: dict[str, Any], *, runtime_root: Path) -> FieldSession:
    key = str(payload.get("session_id") or "").strip()
    if key and key in _SESSIONS:
        return _SESSIONS[key]
    active = _resolve_session_for_stop("")
    if active:
        return active
    created = start_field_session({**payload, "session_status": "FIELD_SESSION_AUTOCREATED_FOR_SHUTTER"}, runtime_root=runtime_root)
    session = _SESSIONS[created["session_id"]]
    _add_reason(session, "FIELD_SESSION_AUTOCREATED_FOR_SHUTTER")
    return session


def _resolve_existing_session(session_id: Any | None, *, runtime_root: Path | None = None) -> FieldSession | None:
    key = str(session_id or "").strip()
    if not key:
        return None
    if key in _SESSIONS:
        return _SESSIONS[key]
    return _load_session_from_disk(key, runtime_root=runtime_root)


def _safe_frame_result(session: FieldSession, *, status: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    tree_status = tree_model_status()
    # Safe skips have no decodable image, so keep the legacy no-model contract
    # for older gates while real image frames can still use the tree candidate.
    model_status = "MODEL_NOT_READY"
    safe_extra = {key: value for key, value in dict(extra or {}).items() if key != "image_bytes"}
    measurement = _frame_measurement(
        {
            "status": status,
            "tree_detected": False,
            "detected_classes": [],
            "tree_confidence": 0.0,
            "tree_bbox_xyxy": None,
            **tree_status,
        }
    )
    return {
        "status": status,
        "http_status": 202,
        "session_id": session.session_id,
        "session_status": session.session_status,
        "model_status": model_status,
        "tree_model_status": tree_status.get("tree_model_status"),
        "pole_model_status": "POLE_MODEL_NOT_READY",
        "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
        "detections": [],
        "detected_classes": [],
        "tree_detected": False,
        "pole_detected": False,
        "conductor_detected": False,
        "no_fake_pole_conductor_detection": True,
        "no_fake_detection": True,
        "no_autosave_on_realtime_frame": True,
        "measurement_result": measurement,
        "overlay_json": {
            "status": "FIELD_SESSION_OVERLAY_READY",
            "message": status if model_status != "MODEL_NOT_READY" else "MODEL_NOT_READY_NO_FAKE_DETECTION",
            "boxes": [],
            "draw_client_side": True,
        },
        **safe_extra,
    }


def _session_frame_result_from_tree(session: FieldSession, tree: dict[str, Any]) -> dict[str, Any]:
    measurement = _frame_measurement(tree)
    model_status = tree.get("model_status") or "MODEL_NOT_READY"
    readiness = tree.get("model_readiness") or model_readiness_status()
    geometry = tree.get("geometry") or {}
    geometry_status = tree.get("geometry_readiness") or geometry.get("geometry_status") or measurement.get("geometry_status")
    return {
        "status": tree.get("status", "FIELD_SESSION_FRAME_PROCESSED"),
        "http_status": 200 if tree.get("status") in {"TREE_MODEL_FRAME_PROCESSED_CANDIDATE", "REALTIME_YOLO_PIPELINE_OK"} else 202,
        "session_id": session.session_id,
        "session_status": session.session_status,
        "model_status": model_status,
        "model_readiness": readiness,
        "tree_model_status": tree.get("tree_model_status") or readiness.get("tree_model_status"),
        "model_source": tree.get("model_source"),
        "production_status": tree.get("production_status", "NOT_FINAL_CANDIDATE_DETECTION"),
        "pole_model_status": tree.get("pole_model_status") or readiness.get("pole_model_status", "POLE_MODEL_NOT_READY"),
        "conductor_model_status": tree.get("conductor_model_status") or readiness.get("conductor_model_status", "CONDUCTOR_MODEL_NOT_READY"),
        "detections": tree.get("detections", []),
        "detected_classes": tree.get("detected_classes", []),
        "tree_detected": bool(tree.get("tree_detected")),
        "tree_confidence": tree.get("tree_confidence", 0.0),
        "tree_bbox_xyxy": tree.get("tree_bbox_xyxy"),
        "pole_detected": bool(tree.get("pole_detected")),
        "conductor_detected": bool(tree.get("conductor_detected")),
        "object_detected": {
            "tree": bool(tree.get("tree_detected")),
            "pole": bool(tree.get("pole_detected")),
            "conductor": bool(tree.get("conductor_detected")),
        },
        "geometry_status": geometry_status,
        "geometry_readiness": tree.get("geometry_readiness") or geometry_status,
        "geometry": geometry,
        "measurement_result": measurement,
        "overlay_json": {
            "status": "FIELD_SESSION_OVERLAY_READY",
            "message": "TREE_MODEL_READY_CANDIDATE" if (tree.get("tree_model_status") or readiness.get("tree_model_status")) == "TREE_MODEL_READY_CANDIDATE" else "MODEL_NOT_READY_NO_FAKE_DETECTION",
            "boxes": tree.get("detections", []),
            "draw_client_side": True,
        },
        "no_autosave_on_realtime_frame": True,
        "no_fake_pole_conductor_detection": True,
        "no_fake_detection": True,
    }


def _frame_measurement(tree: dict[str, Any]) -> dict[str, Any]:
    geometry = tree.get("geometry") or {}
    geometry_status = tree.get("geometry_readiness") or geometry.get("geometry_status") or "INSUFFICIENT_GEOMETRY_DATA"
    reason = [
        "POLE_MODEL_NOT_READY",
        "CONDUCTOR_MODEL_NOT_READY",
        "NO_FAKE_POLE_CONDUCTOR_DETECTION",
        geometry_status,
        "CALIBRATION_NOT_READY",
    ]
    if tree.get("tree_detected"):
        reason.append("TREE_MODEL_READY_CANDIDATE_NOT_FINAL")
    elif tree.get("tree_model_status") == "TREE_MODEL_READY_CANDIDATE":
        reason.append("TREE_NOT_DETECTED_BY_CANDIDATE_MODEL")
    else:
        reason.append("TREE_MODEL_NOT_READY")
    return {
        "status": geometry_status if "BLOCKED" in str(geometry_status) else "INSUFFICIENT_GEOMETRY_DATA",
        "geometry_status": geometry_status,
        "detected_classes": tree.get("detected_classes", []),
        "tree_detected": bool(tree.get("tree_detected")),
        "tree_confidence": tree.get("tree_confidence", 0.0),
        "tree_bbox": tree.get("tree_bbox_xyxy"),
        "pole_detected": bool(tree.get("pole_detected")),
        "conductor_detected": bool(tree.get("conductor_detected")),
        "clearance_m": geometry.get("estimated_clearance_m"),
        "tree_height_m": geometry.get("estimated_tree_height_m"),
        "cable_height_m": geometry.get("estimated_conductor_height_m"),
        "conductor_height_m": geometry.get("estimated_conductor_height_m"),
        "zone_status": "INSUFFICIENT_DATA",
        "risk_level": "INSUFFICIENT_DATA",
        "action_recommendation": "Model pohon kandidat tersedia, tetapi tiang/kabel/kalibrasi belum siap untuk clearance final.",
        "calibration_status": "CALIBRATION_NOT_READY",
        "confidence_status": "NOT_FINAL_CANDIDATE_DETECTION",
        "measurement_quality_label": "INSUFFICIENT_GEOMETRY_DATA",
        "reason_codes": _dedupe(reason),
    }


def _duplicate_shutter_result(session: FieldSession, payload: dict[str, Any]) -> dict[str, Any] | None:
    now = time.time()
    idempotency_key = str(payload.get("idempotency_key") or "").strip()
    fingerprint = _shutter_fingerprint(session, payload)
    cache_key = f"{session.session_id}|{idempotency_key}" if idempotency_key else f"{session.session_id}|{fingerprint}"
    cached = _SHUTTER_IDEMPOTENCY.get(cache_key) or _LAST_SHUTTER_FINGERPRINT.get(f"{session.session_id}|{fingerprint}")
    if cached and now - float(cached.get("created_monotonic", 0)) <= 2.0:
        report = dict(cached.get("result") or {})
        report.update(
            {
                "status": "DUPLICATE_SHUTTER_IGNORED",
                "csv_appended": False,
                "duplicate_ignored": True,
                "idempotency_key": idempotency_key or fingerprint,
                "no_fake_detection": True,
            }
        )
        return report
    return None


def _remember_shutter(session: FieldSession, payload: dict[str, Any], report: dict[str, Any]) -> None:
    now = time.time()
    idempotency_key = str(payload.get("idempotency_key") or "").strip()
    fingerprint = _shutter_fingerprint(session, payload)
    entry = {"created_monotonic": now, "result": dict(report)}
    if idempotency_key:
        _SHUTTER_IDEMPOTENCY[f"{session.session_id}|{idempotency_key}"] = entry
        session.latest_shutter_idempotency_key = idempotency_key
    _LAST_SHUTTER_FINGERPRINT[f"{session.session_id}|{fingerprint}"] = entry


def _shutter_fingerprint(session: FieldSession, payload: dict[str, Any]) -> str:
    image = str(payload.get("image_jpeg_base64") or payload.get("frame_jpeg_base64") or payload.get("image_base64") or "")
    seed = "|".join(
        [
            session.session_id,
            str(payload.get("point_id") or session.point_id),
            str(payload.get("notes") or payload.get("operator_notes") or ""),
            str(session.current_gps.get("latitude")),
            str(session.current_gps.get("longitude")),
            image[:96],
        ]
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _write_session_shutter_image(payload: dict[str, Any], *, runtime_root: Path, report_id: str) -> dict[str, Any]:
    from .progress5_4_field_runtime import _decode_image, MAX_SHUTTER_IMAGE_BYTES

    data = _decode_image(payload.get("image_jpeg_base64") or payload.get("frame_jpeg_base64") or payload.get("image_base64"))
    if data is None:
        return {"status": "SNAPSHOT_IMAGE_NOT_PROVIDED_METADATA_ONLY", "snapshot_path": ""}
    if len(data) > MAX_SHUTTER_IMAGE_BYTES:
        return {"status": "SNAPSHOT_IMAGE_TOO_LARGE_DROPPED_METADATA_ONLY", "snapshot_path": ""}
    output_dir = runtime_root / "field_captures"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_id}.jpg"
    path.write_bytes(data)
    return {"status": "SNAPSHOT_IMAGE_WRITTEN_RUNTIME_ONLY", "snapshot_path": str(path)}


def _session_report_csv(session: FieldSession) -> Path:
    return PROGRESS5_4_REPORT_CSV if session.source_mode == "LIVE_OPERATOR" else SESSION_SMOKE_REPORT_CSV


def _session_start_contract(session_id: str) -> dict[str, Any]:
    readiness = model_readiness_status()
    return {
        "ok": True,
        "camera_url": f"/field-camera?session_id={session_id}",
        "map_enabled": False,
        "result_enabled": False,
        "shutter_required": True,
        "degraded": False,
        "model_readiness": readiness,
        "tree_model_status": readiness.get("tree_model_status"),
        "pole_model_status": readiness.get("pole_model_status", "POLE_MODEL_NOT_READY"),
        "conductor_model_status": readiness.get("conductor_model_status", "CONDUCTOR_MODEL_NOT_READY"),
        "auto_geometry_status": readiness.get("geometry_readiness", "AUTO_GEOMETRY_BLOCKED_WAITING_FOR_POLE_CONDUCTOR_MODEL"),
    }


def _spreadsheet_row(row: dict[str, Any]) -> dict[str, Any]:
    columns = [
        "session_id",
        "timestamp",
        "point_id",
        "operator_name",
        "gps_lat",
        "gps_lon",
        "gps_accuracy_m",
        "horizontal_distance_from_tree_m",
        "distance_reliability_status",
        "tree_detected",
        "tree_confidence",
        "tree_bbox",
        "pole_detected",
        "conductor_detected",
        "model_status",
        "growth_prior_status",
        "growth_model_status",
        "growth_selected_model",
        "growth_validation_mae",
        "growth_validation_rmse",
        "growth_validation_r2",
        "growth_year_m",
        "eta_3m_status",
        "clearance_m",
        "zone_status",
        "map_url",
        "frame_status",
        "source_status",
        "notes",
    ]
    return {column: _spreadsheet_value(row.get(column)) for column in columns}


def _spreadsheet_value(value: Any) -> str:
    if value is None:
        return "NOT_AVAILABLE"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    text = str(value)
    return text if text else ""


def _ensure_report_schema(path: Path) -> None:
    if not path.exists():
        return
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    if fieldnames and set(PROGRESS5_4_REPORT_COLUMNS).issubset(set(fieldnames)):
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROGRESS5_4_REPORT_COLUMNS)
        writer.writeheader()
        for existing in rows:
            writer.writerow({key: existing.get(key, "") for key in PROGRESS5_4_REPORT_COLUMNS})


def _source_mode(payload: dict[str, Any], *, session_id: str = "") -> str:
    explicit = str(payload.get("source_mode") or "").strip().upper()
    if explicit in {"LIVE_OPERATOR", "SMOKE_TEST", "DRY_RUN"}:
        return explicit
    text = " ".join(
        [
            session_id,
            str(payload.get("operator_name") or ""),
            str(payload.get("notes") or payload.get("operator_notes") or ""),
            str(payload.get("point_id") or ""),
        ]
    ).lower()
    if "smoke" in text or "test" in text:
        return "SMOKE_TEST"
    if "dry" in text:
        return "DRY_RUN"
    return "LIVE_OPERATOR"


def _session_map_path(session_id: str, *, runtime_root: Path | None = None) -> Path:
    root = (runtime_root / "field_maps") if runtime_root else SESSION_MAP_DIR
    return root / f"{session_id}.html"


def _short_session(session_id: str) -> str:
    return session_id.replace("FS_", "")[-8:] or uuid.uuid4().hex[:8]


def _get_or_latest(session_id: Any | None = None, *, create_if_missing: bool = False) -> FieldSession:
    key = str(session_id or _LATEST_SESSION_ID or "")
    if key and key in _SESSIONS:
        return _SESSIONS[key]
    if not create_if_missing and key:
        raise KeyError(f"Field session not found: {key}")
    payload = {"session_id": key or f"FS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"}
    start_field_session(payload)
    return _SESSIONS[payload["session_id"]]


def _load_session_from_disk(session_id: str, *, runtime_root: Path | None = None) -> FieldSession | None:
    key = str(session_id or "").strip()
    if not key or key in _SESSIONS:
        return _SESSIONS.get(key)
    root = (runtime_root / "field_sessions") if runtime_root else SESSION_RUNTIME_DIR
    path = root / f"{key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    allowed = {field_name for field_name in FieldSession.__dataclass_fields__}
    session = FieldSession(**{name: data.get(name) for name in allowed if name in data})
    _SESSIONS[session.session_id] = session
    return session


def _save_session(session: FieldSession, *, runtime_root: Path | None = None) -> None:
    root = (runtime_root / "field_sessions") if runtime_root else SESSION_RUNTIME_DIR
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{session.session_id}.json").write_text(json.dumps(asdict(session), indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "latest.json").write_text(json.dumps(asdict(session), indent=2, ensure_ascii=False), encoding="utf-8")


def log_session_exception(exc: Exception, *, route: str, runtime_root: Path | None = None) -> dict[str, Any]:
    date = datetime.now().strftime("%Y%m%d")
    candidate_root = runtime_root or (PROJECT_ROOT / "data" / "runtime")
    path = candidate_root / "session_errors" / f"field_session_error_{date}.jsonl"
    payload = {"timestamp": datetime.now().isoformat(), "route": route, "error_type": type(exc).__name__, "message": str(exc)[:500]}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        path = SESSION_ERROR_DIR / f"field_session_error_{date}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return {"status": "FIELD_SESSION_ROUTE_EXCEPTION_LOGGED", "error_log": str(path), **payload}


def _base_result(model_status: str) -> dict[str, Any]:
    return {
        "status": "MODEL_NOT_READY_NO_FAKE_DETECTION" if model_status == "MODEL_NOT_READY" else "FIELD_RESULT_PROVISIONAL",
        "model_status": model_status,
        "geometry_status": "INSUFFICIENT_GEOMETRY_DATA",
        "reason_codes": ["MODEL_NOT_READY_NO_FAKE_DETECTION" if model_status == "MODEL_NOT_READY" else "FIELD_RESULT_PROVISIONAL"],
    }


def _basic_map_html(
    lat: Any,
    lon: Any,
    point_id: str,
    *,
    session: FieldSession,
    derived: dict[str, Any],
    gps_truth: dict[str, Any],
    base_truth: dict[str, Any] | None = None,
) -> str:
    if lat is None or lon is None:
        marker = (
            "<p>Status: NO_GPS_NO_MARKER</p>"
            "<p>GPS belum valid, marker tidak dibuat.</p>"
            f"<p>GPS precision status: {html.escape(str(gps_truth.get('gps_precision_status')))}</p>"
            f"<p>Reason: {html.escape(';'.join(str(item) for item in gps_truth.get('gps_quality_reasons', [])))}</p>"
        )
    else:
        base = session.base_gps
        base_lines = ""
        if base_truth and base_truth.get("marker_allowed"):
            base_lines = (
                f"<p>Base marker bawah pohon: {html.escape(format_coordinate_raw(base.get('latitude')))}, "
                f"{html.escape(format_coordinate_raw(base.get('longitude')))}</p>"
            )
        marker = (
            "<p>Status: MAP_HTML_READY</p>"
            f"{base_lines}"
            f"<p>Current marker operator/kamera: {html.escape(format_coordinate_raw(lat))}, {html.escape(format_coordinate_raw(lon))}</p>"
            f"<p>Accuracy: {html.escape(str(session.current_gps.get('accuracy')))} m</p>"
            f"<p>Accuracy circle radius: {html.escape(str(session.current_gps.get('accuracy')))} m</p>"
            "<p>Polyline: base marker ke current marker.</p>"
        )
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Field Session Map</title>
<style>
body{{margin:0;min-height:100dvh;font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#eefdf3;background:
radial-gradient(circle at 20% 10%,rgba(75,196,126,.28),transparent 28%),
linear-gradient(135deg,#071c14,#123827 54%,#06120d);overflow-wrap:anywhere;word-break:break-word}}
main{{max-width:760px;margin:0 auto;padding:22px}}
.card{{border:1px solid rgba(220,255,232,.22);border-radius:28px;background:rgba(9,42,30,.62);backdrop-filter:blur(18px);box-shadow:0 24px 70px rgba(0,0,0,.28);padding:18px;overflow:hidden}}
.pill{{display:inline-flex;margin:4px 4px 4px 0;padding:7px 10px;border-radius:999px;background:rgba(215,255,226,.13);border:1px solid rgba(230,255,236,.18);font-size:12px}}
a{{color:#d9ffe6}}
</style></head>
<body><main><section class="card"><p class="pill">{'MAP_HTML_READY' if lat is not None and lon is not None else 'NO_GPS_NO_MARKER'}</p><p class="pill">{html.escape(str(gps_truth.get('gps_precision_status')))}</p>
<h1>Field Session Map</h1>
<p>Session: {html.escape(session.session_id)}</p>
<p>Point: {html.escape(point_id)}</p>{marker}
<p>Distance reliability: {html.escape(str(derived.get('distance_reliability_status')))}</p>
<p>Horizontal distance from tree: {html.escape(str(derived.get('horizontal_distance_from_tree_m')))}</p>
<p>GPS digunakan sebagai evidence lokasi dan jarak horizontal kasar; bukan kalibrasi pixel-to-meter.</p>
<p><a href="/field-camera?session_id={html.escape(session.session_id)}">Back to Camera</a></p>
</section></main></body></html>"""


def _apply_visibility_payload(session: FieldSession, payload: dict[str, Any]) -> None:
    visibility = str(payload.get("visibility_state") or "").strip()
    if visibility:
        session.visibility_state = visibility
    foreground = str(payload.get("foreground_recording_status") or "").strip()
    if foreground:
        session.foreground_recording_status = foreground
    hidden_started = str(payload.get("hidden_started_at") or "").strip()
    if hidden_started:
        session.hidden_started_at = hidden_started
    hidden_duration = _to_int(payload.get("hidden_duration_ms"))
    if hidden_duration is not None:
        session.hidden_duration_ms = hidden_duration
    if "frame_loop_paused_due_to_hidden" in payload:
        session.frame_loop_paused_due_to_hidden = _bool(payload.get("frame_loop_paused_due_to_hidden"))
    warning = str(payload.get("browser_throttle_warning") or "").strip()
    if warning:
        session.browser_throttle_warning = warning
    if session.visibility_state == "hidden":
        session.foreground_recording_status = "PAGE_HIDDEN_BROWSER_MAY_THROTTLE"
        session.frame_loop_paused_due_to_hidden = True
        if not session.browser_throttle_warning:
            session.browser_throttle_warning = "Halaman tidak aktif. Browser dapat membatasi kamera/timer/GPS."
        _add_reason(session, "RECORDING_MAY_BE_THROTTLED")
    elif session.foreground_recording_status in {"", "FOREGROUND_RECORDING_REQUIRED"} and session.session_status == "RECORDING_ACTIVE":
        session.foreground_recording_status = "FOREGROUND_RECORDING_ACTIVE"


def _add_reason(session: FieldSession, reason: str) -> None:
    if reason and reason not in session.reason_codes:
        session.reason_codes.append(reason)


def _dedupe(values: list[Any]) -> list[str]:
    seen: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in seen:
            seen.append(text)
    return seen


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _first_present(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload.get(key) not in {None, ""}:
            return payload.get(key)
    return None
