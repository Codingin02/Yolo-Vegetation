"""Phase 16 remote realtime frame session layer.

This module keeps realtime frame handling separate from the Phase 9 upload
flow. Realtime frames are latest-only, rate-limited to 1 FPS by default, and
do not write spreadsheet/map reports unless a snapshot endpoint explicitly
requests it.
"""

from __future__ import annotations

import base64
import json
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .auto_measurement import measure_from_detections, run_auto_measurement_for_image
from .job_queue import RUNTIME_ROOT
from .phase9_monitoring import append_monitoring_row, build_phase9_monitoring_row, write_phase9_risk_map
from .realtime_eta_pipeline import run_realtime_eta_pipeline
from .realtime_inference_contract import infer_realtime_frame
from .safety_clearance_policy import classify_distance_zone, eta_status_from_days
from .temporal_stabilizer import TemporalStabilizer
from .yolo_model_resolver import resolve_yolo_model

MAX_FRAME_SIZE_BYTES = 1_500_000
DEFAULT_FRAME_INTERVAL_MS = 1000
MAX_STALE_FRAME_MS = 3000
MAX_CLIENTS = 2
REPORT_COOLDOWN_SEC = 45
SESSION_DIR = RUNTIME_ROOT / "realtime_sessions"


@dataclass
class RealtimeSession:
    session_id: str
    token: str
    created_at: float = field(default_factory=time.time)
    last_frame_at: float = 0.0
    last_report_at: float = 0.0
    latest_result: dict[str, Any] = field(default_factory=lambda: {"status": "NO_REALTIME_RESULT_YET"})
    stabilizer: TemporalStabilizer = field(default_factory=lambda: TemporalStabilizer(window_size=5, min_samples=3))
    dropped_frames: int = 0
    processed_frames: int = 0


_SESSIONS: dict[str, RealtimeSession] = {}


def create_realtime_session(runtime_root: Path = RUNTIME_ROOT) -> dict[str, Any]:
    if len(_SESSIONS) >= MAX_CLIENTS:
        stale = sorted(_SESSIONS.items(), key=lambda item: item[1].created_at)[0][0]
        _SESSIONS.pop(stale, None)
    session = RealtimeSession(session_id=f"rt_{secrets.token_hex(8)}", token=secrets.token_urlsafe(18))
    _SESSIONS[session.session_id] = session
    _persist_session(session, runtime_root)
    return {
        "status": "REALTIME_SESSION_CREATED",
        "session_id": session.session_id,
        "session_token": session.token,
        "ws_path": "/ws/realtime-detect",
        "fallback_frame_endpoint": "/api/realtime/frame",
        "report_snapshot_endpoint": "/api/realtime/report-snapshot",
        "requested_interval_ms": DEFAULT_FRAME_INTERVAL_MS,
        "max_stale_frame_ms": MAX_STALE_FRAME_MS,
        "max_frame_size_bytes": MAX_FRAME_SIZE_BYTES,
        "security_note": "Token runtime disimpan di data/runtime yang di-ignore; jangan commit token.",
    }


def get_session_status(session_id: str) -> dict[str, Any]:
    session = _SESSIONS.get(session_id)
    if session is None:
        return {"status": "REALTIME_SESSION_NOT_FOUND", "session_id": session_id}
    return {
        "status": "REALTIME_SESSION_READY",
        "session_id": session.session_id,
        "created_at": session.created_at,
        "processed_frames": session.processed_frames,
        "dropped_frames": session.dropped_frames,
        "latest_result_status": session.latest_result.get("status"),
        "queue_policy": "LATEST_ONLY_DROP_OLD_FRAMES",
        "requested_interval_ms": DEFAULT_FRAME_INTERVAL_MS,
        "max_stale_frame_ms": MAX_STALE_FRAME_MS,
    }


def validate_session_token(session_id: str, token: str | None) -> bool:
    session = _SESSIONS.get(session_id)
    return session is not None and session.token == str(token or "")


def latest_realtime_result(session_id: str) -> dict[str, Any]:
    session = _SESSIONS.get(session_id)
    if session is None:
        return {"status": "REALTIME_SESSION_NOT_FOUND", "session_id": session_id}
    return session.latest_result


def validate_realtime_payload_contract(payload: dict[str, Any]) -> dict[str, Any]:
    required = {
        "session_id",
        "frame_id",
        "timestamp_client_ms",
        "point_id",
        "species_hint",
        "asset_type",
        "client_mode",
        "requested_interval_ms",
    }
    missing = sorted(name for name in required if name not in payload)
    return {
        "status": "WEBSOCKET_PAYLOAD_CONTRACT_VALID" if not missing else "WEBSOCKET_PAYLOAD_CONTRACT_MISSING_FIELDS",
        "missing": missing,
        "required_fields": sorted(required),
    }


def process_realtime_frame(payload: dict[str, Any], *, demo_mock: bool = False, write_report: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    contract = validate_realtime_payload_contract(payload)
    if contract["missing"]:
        return _result(payload, "REALTIME_PAYLOAD_INVALID", contract=contract, started=started)

    session = _SESSIONS.get(str(payload.get("session_id")))
    if session is None:
        return _result(payload, "REALTIME_SESSION_NOT_FOUND", started=started)
    if not _token_ok(session, payload):
        return _result(payload, "REALTIME_SESSION_TOKEN_INVALID", started=started)

    stale = _frame_age_ms(payload)
    if stale is not None and stale > MAX_STALE_FRAME_MS:
        session.dropped_frames += 1
        result = _result(payload, "STALE_FRAME_DROPPED", queue_status="DROPPED_STALE_FRAME", started=started)
        session.latest_result = result
        return result

    now = time.monotonic()
    if (now - session.last_frame_at) * 1000 < DEFAULT_FRAME_INTERVAL_MS:
        session.dropped_frames += 1
        result = _result(payload, "FRAME_RATE_LIMITED", queue_status="DROPPED_RATE_LIMIT_1FPS", started=started)
        session.latest_result = result
        return result
    session.last_frame_at = now
    session.processed_frames += 1

    image_status = _image_payload_status(payload)
    if image_status in {"FRAME_TOO_LARGE_DROPPED", "IMAGE_BASE64_INVALID"}:
        session.dropped_frames += 1
        result = _result(
            payload,
            image_status,
            queue_status=image_status,
            started=started,
            image_status=image_status,
            detections=[],
            model_status=resolve_yolo_model()["status"],
            detection_status="NO_FAKE_DETECTION_FRAME_REJECTED",
            reason_codes=[image_status],
        )
        session.latest_result = result
        return result
    model = resolve_yolo_model()
    inference_contract = infer_realtime_frame(None, demo_mock=demo_mock)
    if demo_mock:
        measurement = measure_from_detections(_mock_phase16_detections(), asset_profile={"pole_height_reference_m": 12}, point_id=str(payload.get("point_id", "")))
        measurement["model_status"] = "DEMO_MOCK_NOT_REAL_FIELD_RESULT"
    elif model["status"] == "MODEL_NOT_READY":
        measurement = run_auto_measurement_for_image(None, point_id=str(payload.get("point_id", "")))
    else:
        measurement = {
            **run_auto_measurement_for_image(None, point_id=str(payload.get("point_id", ""))),
            "model_status": model["status"],
            "reason": "Custom model detected but live YOLO inference execution is deferred to adapter validation; no fake detection emitted.",
        }

    selected_clearance = measurement.get("stabilized_clearance_m") or measurement.get("selected_clearance_m")
    zone = classify_distance_zone(selected_clearance)
    eta = run_realtime_eta_pipeline(
        {
            **measurement,
            "selected_clearance_m": selected_clearance,
            "selected_hazard_target": measurement.get("selected_hazard_target", "unknown"),
        },
        species=str(payload.get("species_hint") or "pohon_sono"),
        point_id=str(payload.get("point_id") or ""),
        latitude=payload.get("gps_lat"),
        longitude=payload.get("gps_lon"),
    )
    eta_priority = eta_status_from_days(eta.get("eta_days"))
    risk_priority = eta_priority["risk_priority"] if eta_priority["risk_priority"] != "INSUFFICIENT_DATA" else eta.get("risk_priority")
    if zone["distance_zone_status"] in {"CONTACT_OR_OVERLAP", "UNSAFE_WITHIN_3M"} and risk_priority in {None, "", "LOW", "INSUFFICIENT_DATA"}:
        risk_priority = "CRITICAL" if zone["distance_zone_status"] == "CONTACT_OR_OVERLAP" else "HIGH"

    overlay = build_overlay_json(measurement, zone, eta, payload)
    queue_status = "HIGH_LATENCY_DROPPING_OLD_FRAMES" if _elapsed_ms(started) > MAX_STALE_FRAME_MS else "LATEST_ONLY_OK"
    result = _result(
        payload,
        "REALTIME_FRAME_PROCESSED",
        queue_status=queue_status,
        started=started,
        image_status=image_status,
        inference_contract=inference_contract,
        model_status=measurement.get("model_status", model["status"]),
        detection_status="NO_FAKE_DETECTION_MODEL_NOT_READY" if measurement.get("model_status") == "MODEL_NOT_READY" else measurement.get("measurement_status"),
        measurement_status=measurement.get("measurement_status"),
        eta_status=eta_priority["eta_status"],
        overlay_json=overlay,
        detections=measurement.get("detected_objects", []),
        selected_clearance_m_raw=measurement.get("selected_clearance_m"),
        selected_clearance_m_stable=selected_clearance,
        selected_clearance_display_m=zone["selected_clearance_display_m"],
        selected_hazard_target=measurement.get("selected_hazard_target", "unknown"),
        safe_clearance_min_m=zone["safe_clearance_min_m"],
        distance_zone_status=zone["distance_zone_status"],
        risk_priority=risk_priority,
        action_recommendation=zone["distance_zone_action"] if zone["distance_zone_status"] != "SAFE" else eta.get("action_recommendation"),
        eta_days=eta.get("eta_days"),
        eta_months=eta.get("eta_months"),
        confidence_status=eta.get("confidence_status") or measurement.get("measurement_confidence"),
        reason=measurement.get("reason") or eta.get("reason"),
    )
    session.latest_result = result
    if write_report:
        result.update(write_realtime_snapshot_report(session.session_id, result, "explicit_snapshot"))
    return result


def write_realtime_snapshot_report(session_id: str, latest_result: dict[str, Any] | None = None, report_trigger: str = "operator_snapshot") -> dict[str, Any]:
    session = _SESSIONS.get(session_id)
    result = latest_result or (session.latest_result if session else None)
    if not result or result.get("status") in {"NO_REALTIME_RESULT_YET", "REALTIME_SESSION_NOT_FOUND"}:
        return {"report_status": "NO_STABLE_REALTIME_RESULT_TO_REPORT", "report_written": False}
    now = time.monotonic()
    if session and report_trigger != "operator_snapshot" and now - session.last_report_at < REPORT_COOLDOWN_SEC:
        return {"report_status": "REPORT_COOLDOWN_ACTIVE", "report_written": False, "cooldown_sec": REPORT_COOLDOWN_SEC}
    row = build_phase9_monitoring_row(
        {
            "inspection_id": result.get("session_id", session_id),
            "job_id": result.get("frame_id", ""),
            "point_id": result.get("point_id", ""),
            "species": result.get("species_hint", "pohon_sono"),
            "asset_type": result.get("asset_type", "span"),
            "latitude": result.get("gps", {}).get("lat", ""),
            "longitude": result.get("gps", {}).get("lon", ""),
            "eta_days": result.get("eta_days", ""),
            "eta_months": result.get("eta_months", ""),
            "risk_priority": result.get("risk_priority", ""),
            "action_recommendation": result.get("action_recommendation", ""),
            "selected_clearance_m_raw": result.get("selected_clearance_m_raw", ""),
            "selected_clearance_m_stable": result.get("selected_clearance_m_stable", ""),
            "selected_clearance_display_m": result.get("selected_clearance_display_m", ""),
            "safe_clearance_min_m": result.get("safe_clearance_min_m", ""),
            "distance_zone_status": result.get("distance_zone_status", ""),
            "selected_hazard_target": result.get("selected_hazard_target", ""),
            "report_trigger": report_trigger,
            "realtime_session_id": session_id,
            "frame_id_snapshot": result.get("frame_id", ""),
            "model_status": result.get("model_status", ""),
            "confidence_status": result.get("confidence_status", ""),
            "mode": "REALTIME_SNAPSHOT",
            "reason": result.get("reason", ""),
            "operator_notes": f"report_trigger={report_trigger}; realtime_session_id={session_id}; frame_id_snapshot={result.get('frame_id', '')}",
        }
    )
    csv_result = append_monitoring_row(row)
    map_result = write_phase9_risk_map(row)
    if session:
        session.last_report_at = now
    return {
        "report_status": csv_result.get("status"),
        "report_written": bool(csv_result.get("written")),
        "report_path": csv_result.get("path"),
        "map_status": map_result.get("status"),
        "map_marker_written": bool(map_result.get("written")),
        "map_path": map_result.get("path"),
        "report_trigger": report_trigger,
    }


def build_overlay_json(measurement: dict[str, Any], zone: dict[str, Any], eta: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    boxes = []
    for item in measurement.get("detected_objects", []) or []:
        if isinstance(item, dict):
            boxes.append(
                {
                    "label": item.get("class_name"),
                    "bbox": item.get("bbox"),
                    "confidence": item.get("confidence"),
                    "color": _label_color(str(item.get("class_name", ""))),
                }
            )
    return {
        "status": "OVERLAY_JSON_READY",
        "boxes": boxes,
        "distance_line": {
            "status": "AVAILABLE_IF_HAZARD_TARGET_DETECTED" if measurement.get("selected_clearance_m") is not None else "NOT_AVAILABLE",
            "clearance_m": measurement.get("selected_clearance_m"),
            "stable_clearance_m": measurement.get("stabilized_clearance_m") or measurement.get("selected_clearance_m"),
        },
        "safe_zone": {"safe_clearance_min_m": zone["safe_clearance_min_m"], "distance_zone_status": zone["distance_zone_status"]},
        "risk_label": eta.get("risk_priority"),
        "eta_label": {"eta_days": eta.get("eta_days"), "eta_months": eta.get("eta_months")},
        "latency_ms": payload.get("latency_ms"),
        "draw_client_side": True,
    }


def websocket_available() -> dict[str, Any]:
    try:
        import flask_sock  # noqa: F401
    except ImportError:
        return {"status": "WEBSOCKET_DEPENDENCY_NOT_INSTALLED", "package": "flask-sock", "fallback": "HTTP_POLLING_1FPS"}
    return {"status": "WEBSOCKET_AVAILABLE", "package": "flask-sock", "fallback": "HTTP_POLLING_1FPS"}


def _result(payload: dict[str, Any], status: str, *, started: float, **extra: Any) -> dict[str, Any]:
    return {
        "status": status,
        "session_id": payload.get("session_id", ""),
        "frame_id": payload.get("frame_id", ""),
        "point_id": payload.get("point_id", ""),
        "species_hint": payload.get("species_hint", "pohon_sono"),
        "asset_type": payload.get("asset_type", "span"),
        "timestamp_server_ms": int(time.time() * 1000),
        "latency_ms": _latency_ms(payload),
        "processing_time_ms": _elapsed_ms(started),
        "queue_status": extra.pop("queue_status", "LATEST_ONLY_IDLE"),
        "gps": {"lat": payload.get("gps_lat"), "lon": payload.get("gps_lon"), "status": "GPS_READY" if payload.get("gps_lat") and payload.get("gps_lon") else "GPS_NOT_READY"},
        "overlay_image_jpeg_base64": None,
        "not_accuracy_claim": True,
        "no_fake_detection": True,
        **extra,
    }


def _persist_session(session: RealtimeSession, runtime_root: Path) -> None:
    path = runtime_root / "realtime_sessions" / f"{session.session_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"session_id": session.session_id, "token": session.token, "created_at": session.created_at}, indent=2), encoding="utf-8")


def _token_ok(session: RealtimeSession, payload: dict[str, Any]) -> bool:
    return str(payload.get("session_token") or "") == session.token


def _frame_age_ms(payload: dict[str, Any]) -> float | None:
    try:
        return int(time.time() * 1000) - float(payload.get("timestamp_client_ms"))
    except (TypeError, ValueError):
        return None


def _latency_ms(payload: dict[str, Any]) -> int | None:
    age = _frame_age_ms(payload)
    return int(age) if age is not None else None


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _image_payload_status(payload: dict[str, Any]) -> str:
    encoded = payload.get("image_jpeg_base64") or ""
    if not encoded:
        return "NO_IMAGE_PAYLOAD_PREVIEW_ONLY"
    try:
        size = len(base64.b64decode(str(encoded), validate=False))
    except Exception:
        return "IMAGE_BASE64_INVALID"
    if size > MAX_FRAME_SIZE_BYTES:
        return "FRAME_TOO_LARGE_DROPPED"
    return "IMAGE_PAYLOAD_ACCEPTED"


def _mock_phase16_detections() -> list[dict[str, Any]]:
    return [
        {"class_name": "struktur_penyangga", "bbox": [100, 100, 140, 500], "confidence": 0.88},
        {"class_name": "pohon_sono", "bbox": [250, 260, 320, 500], "confidence": 0.82},
        {"class_name": "konduktor", "bbox": [80, 180, 360, 190], "confidence": 0.79},
    ]


def _label_color(label: str) -> str:
    if label == "pohon_sono":
        return "#1b7f3a"
    if label in {"konduktor", "span"}:
        return "#f0a000"
    if label in {"struktur_penyangga", "trafo"}:
        return "#2f6fed"
    return "#777777"
