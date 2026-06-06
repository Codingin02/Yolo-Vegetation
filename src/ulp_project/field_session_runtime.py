"""Native browser GPS/camera field session runtime."""

from __future__ import annotations

import csv
import html
import json
import math
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT
from .progress5_4_field_runtime import (
    PROGRESS5_4_REPORT_COLUMNS,
    PROGRESS5_4_REPORT_CSV,
    ensure_progress5_4_report_schema,
    latest_progress5_4_map,
    latest_progress5_4_measurement,
    process_progress5_4_realtime_frame,
    write_progress5_4_shutter_capture,
)

SESSION_RUNTIME_DIR = PROJECT_ROOT / "outputs" / "runtime" / "field_sessions"
SESSION_MAP_PATH = PROJECT_ROOT / "outputs" / "maps" / "field_session_latest_map.html"

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
    "manual_input_status",
    "page_source",
    "result_page_url",
    "report_page_url",
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
    reason_codes: list[str] = field(default_factory=lambda: ["FOREGROUND_RECORDING_REQUIRED"])


_SESSIONS: dict[str, FieldSession] = {}
_LATEST_SESSION_ID = ""
_LATEST_MANUAL_INPUT: dict[str, Any] = {"status": "NO_MANUAL_INPUT_YET"}


def gps_accuracy_status(accuracy_m: Any) -> dict[str, Any]:
    accuracy = _to_float(accuracy_m)
    if accuracy is None:
        return {"gps_accuracy_status": "GPS_NOT_READY", "gps_quality_reason": "GPS_ACCURACY_UNKNOWN"}
    if accuracy <= 5.0:
        return {"gps_accuracy_status": "GPS_ACCURACY_GOOD", "gps_quality_reason": "GPS_ACCURACY_LE_5M"}
    if accuracy <= 10.0:
        return {"gps_accuracy_status": "GPS_ACCURACY_MEDIUM", "gps_quality_reason": "GPS_ACCURACY_5_TO_10M"}
    return {"gps_accuracy_status": "GPS_ACCURACY_LOW", "gps_quality_reason": "GPS_ACCURACY_GT_10M"}


def compute_haversine_meters(base: dict[str, Any] | None, current: dict[str, Any] | None) -> float | None:
    if not base or not current:
        return None
    lat1 = _to_float(base.get("latitude"))
    lon1 = _to_float(base.get("longitude"))
    lat2 = _to_float(current.get("latitude"))
    lon2 = _to_float(current.get("longitude"))
    if None in {lat1, lon1, lat2, lon2}:
        return None
    radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return round(radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 3)


def distance_reliability(base: dict[str, Any] | None, current: dict[str, Any] | None) -> dict[str, Any]:
    distance = compute_haversine_meters(base, current)
    base_accuracy = _to_float((base or {}).get("accuracy"))
    current_accuracy = _to_float((current or {}).get("accuracy"))
    accuracy_status = gps_accuracy_status(current_accuracy)
    if distance is None:
        return {
            **accuracy_status,
            "horizontal_distance_from_tree_m": None,
            "distance_reliability_status": "GPS_NOT_READY",
            "is_distance_reliable": False,
            "movement_status": "GPS_NOT_READY",
        }
    if base_accuracy is None or current_accuracy is None:
        return {
            **accuracy_status,
            "horizontal_distance_from_tree_m": distance,
            "distance_reliability_status": "GPS_ACCURACY_UNKNOWN",
            "is_distance_reliable": False,
            "movement_status": "MOVED_FROM_TREE_BASE" if distance > 0.5 else "AT_TREE_BASE",
        }
    if max(base_accuracy, current_accuracy) > distance:
        return {
            **accuracy_status,
            "horizontal_distance_from_tree_m": distance,
            "distance_reliability_status": "GPS_ACCURACY_GREATER_THAN_DISTANCE",
            "is_distance_reliable": False,
            "movement_status": "MOVED_FROM_TREE_BASE" if distance > 0.5 else "AT_TREE_BASE",
        }
    return {
        **accuracy_status,
        "horizontal_distance_from_tree_m": distance,
        "distance_reliability_status": "DISTANCE_RELIABLE_WITH_BROWSER_GPS_LIMITS",
        "is_distance_reliable": True,
        "movement_status": "MOVED_FROM_TREE_BASE" if distance > 0.5 else "AT_TREE_BASE",
    }


def normalize_gps(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "latitude": _to_float(payload.get("latitude") or payload.get("gps_lat") or payload.get("lat")),
        "longitude": _to_float(payload.get("longitude") or payload.get("gps_lon") or payload.get("lon")),
        "accuracy": _to_float(payload.get("accuracy") or payload.get("gps_accuracy_m")),
        "altitude": _to_float(payload.get("altitude")),
        "altitudeAccuracy": _to_float(payload.get("altitudeAccuracy") or payload.get("altitude_accuracy")),
        "heading": _to_float(payload.get("heading")),
        "speed": _to_float(payload.get("speed")),
        "timestamp": payload.get("timestamp") or datetime.now().isoformat(),
        "source": payload.get("source") or payload.get("gps_source") or "GPS_SOURCE_BROWSER",
    }


def start_field_session(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    global _LATEST_SESSION_ID
    session_id = str(payload.get("session_id") or f"FS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    base = normalize_gps(payload.get("base_gps") or payload)
    model = check_model_handoff()
    session = FieldSession(
        session_id=session_id,
        point_id=str(payload.get("point_id") or "V001_pohon_sono"),
        operator_name=str(payload.get("operator_name") or ""),
        started_at=datetime.now().isoformat(),
        session_status="RECORDING_ACTIVE",
        secure_context_status=str(payload.get("secure_context_status") or "SECURE_CONTEXT_UNKNOWN"),
        public_tunnel_status=str(payload.get("public_tunnel_status") or "PUBLIC_TUNNEL_NOT_RUNNING"),
        base_gps=base,
        current_gps=base,
        gps_history=[base] if base.get("latitude") is not None and base.get("longitude") is not None else [],
        camera_status=str(payload.get("camera_status") or "CAMERA_WAITING_PERMISSION"),
        model_status=model.get("model_status", "MODEL_NOT_READY"),
        latest_result=_base_result(model.get("model_status", "MODEL_NOT_READY")),
        reason_codes=["FOREGROUND_RECORDING_REQUIRED", "BROWSER_GEOLOCATION_NATIVE_HIGH_ACCURACY_REQUESTED"],
    )
    _SESSIONS[session_id] = session
    _LATEST_SESSION_ID = session_id
    _save_session(session, runtime_root=runtime_root)
    return {**session_status(session_id), "status": "FIELD_SESSION_STARTED"}


def stop_field_session(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    session = _get_or_latest(payload.get("session_id"))
    session.session_status = "RECORDING_STOPPED"
    session.stopped_at = datetime.now().isoformat()
    if "FOREGROUND_RECORDING_REQUIRED" not in session.reason_codes:
        session.reason_codes.append("FOREGROUND_RECORDING_REQUIRED")
    _save_session(session, runtime_root=runtime_root)
    return {**session_status(session.session_id), "status": "FIELD_SESSION_STOPPED"}


def update_field_session_gps(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    session = _get_or_latest(payload.get("session_id"))
    gps = normalize_gps(payload)
    if not session.base_gps or payload.get("set_base"):
        session.base_gps = gps
    session.current_gps = gps
    session.gps_history.append(gps)
    derived = distance_reliability(session.base_gps, session.current_gps)
    session.latest_result = {**session.latest_result, **derived}
    if derived["gps_accuracy_status"] == "GPS_ACCURACY_LOW":
        _add_reason(session, "GPS_ACCURACY_LOW")
    if not derived["is_distance_reliable"]:
        _add_reason(session, str(derived["distance_reliability_status"]))
    _save_session(session, runtime_root=runtime_root)
    return {"status": "FIELD_SESSION_GPS_UPDATED", "session_id": session.session_id, "gps": gps, "derived_gps": derived, "no_fake_gps": True}


def process_field_session_frame(payload: dict[str, Any], *, runtime_root: Path) -> dict[str, Any]:
    session = _get_or_latest(payload.get("session_id"))
    result = process_progress5_4_realtime_frame(payload, runtime_root=runtime_root, debug_coco=bool(payload.get("debug_coco")))
    session.latest_frame_status = result
    session.latest_measurement = result.get("measurement_result", {})
    session.model_status = result.get("model_status", session.model_status)
    session.latest_result = build_latest_result(session.session_id, frame_result=result)
    _save_session(session, runtime_root=runtime_root)
    return {**result, "session_id": session.session_id, "session_status": session.session_status}


def shutter_field_session(payload: dict[str, Any], *, runtime_root: Path) -> dict[str, Any]:
    session = _get_or_latest(payload.get("session_id"))
    payload = dict(payload)
    payload.setdefault("point_id", session.point_id)
    payload.setdefault("operator_name", session.operator_name)
    payload.setdefault("model_status", session.model_status)
    payload.setdefault("gps_lat", session.current_gps.get("latitude"))
    payload.setdefault("gps_lon", session.current_gps.get("longitude"))
    payload.setdefault("gps_accuracy_m", session.current_gps.get("accuracy"))
    payload.setdefault("gps_source", session.current_gps.get("source", "GPS_SOURCE_BROWSER"))
    payload.setdefault("latest_measurement", session.latest_measurement)
    report = write_progress5_4_shutter_capture(payload, runtime_root=runtime_root)
    session.latest_report = {
        **report,
        **_session_row_fields(session, page_source="field_session_shutter"),
        "status": "FIELD_SESSION_REPORT_WRITTEN",
        "report_page_url": f"/field-report?session_id={session.session_id}",
        "result_page_url": f"/field-result?session_id={session.session_id}",
    }
    append_session_report_row(session, session.latest_report)
    _save_session(session, runtime_root=runtime_root)
    return session.latest_report


def record_manual_input(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    global _LATEST_MANUAL_INPUT
    session = _get_or_latest(payload.get("session_id"), create_if_missing=True)
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
    return {
        "status": "FIELD_SESSION_STATUS_READY",
        "session": asdict(session),
        "session_id": session.session_id,
        "session_status": session.session_status,
        "recording_status": session.session_status,
        "foreground_recording_status": "FOREGROUND_RECORDING_REQUIRED",
        "gps": {"base": session.base_gps, "current": session.current_gps, "history_count": len(session.gps_history)},
        "derived_gps": derived,
        "camera_status": session.camera_status,
        "model_status": session.model_status,
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
    reason_codes = list(session.reason_codes)
    if model_status == "MODEL_NOT_READY":
        status = "MODEL_NOT_READY_NO_FAKE_DETECTION"
        reason_codes.append("MODEL_NOT_READY_NO_FAKE_DETECTION")
    if not measurement.get("clearance_m"):
        reason_codes.append("INSUFFICIENT_GEOMETRY_DATA")
    result = {
        "status": status,
        "session_id": session.session_id,
        "model_status": model_status,
        "geometry_status": "INSUFFICIENT_GEOMETRY_DATA" if not measurement.get("clearance_m") else "GEOMETRY_PROVISIONAL",
        "gps_quality_status": derived["gps_accuracy_status"],
        "risk_zone": measurement.get("zone_status") or "INSUFFICIENT_DATA",
        "clearance_m": measurement.get("clearance_m"),
        "eta_days": measurement.get("eta_days"),
        "field_result_disclaimer": "FIELD_RESULT_PROVISIONAL",
        "reason_codes": _dedupe(reason_codes),
        **derived,
        "no_fake_gps": True,
        "no_fake_detection": True,
    }
    session.latest_result = result
    return result


def latest_field_session_report(session_id: Any | None = None) -> dict[str, Any]:
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
    }


def latest_field_session_map(session_id: Any | None = None) -> dict[str, Any]:
    session = _get_or_latest(session_id, create_if_missing=True)
    current = session.current_gps
    if current.get("latitude") is None or current.get("longitude") is None:
        return {"status": "NO_GPS_NO_MARKER", "session_id": session.session_id, "map_exists": False}
    SESSION_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSION_MAP_PATH.write_text(
        _basic_map_html(current.get("latitude"), current.get("longitude"), session.point_id),
        encoding="utf-8",
    )
    return {
        "status": "MAP_BASIC_FALLBACK",
        "session_id": session.session_id,
        "path": str(SESSION_MAP_PATH),
        "map_url": f"/field-maps/{SESSION_MAP_PATH.name}",
        "map_exists": True,
        "fallback": latest_progress5_4_map(),
    }


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


def append_session_report_row(session: FieldSession, report: dict[str, Any]) -> None:
    PROGRESS5_4_REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    ensure_progress5_4_report_schema()
    write_header = not PROGRESS5_4_REPORT_CSV.exists()
    row = {key: "" for key in PROGRESS5_4_REPORT_COLUMNS}
    row.update(report.get("row") or {})
    row.update(_session_row_fields(session, page_source=report.get("page_source") or "field_session"))
    row["csv_path"] = str(PROGRESS5_4_REPORT_CSV)
    with PROGRESS5_4_REPORT_CSV.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROGRESS5_4_REPORT_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in PROGRESS5_4_REPORT_COLUMNS})


def _session_row_fields(session: FieldSession, *, page_source: str) -> dict[str, Any]:
    derived = distance_reliability(session.base_gps, session.current_gps)
    return {
        "session_id": session.session_id,
        "recording_status": session.session_status,
        "base_latitude": session.base_gps.get("latitude"),
        "base_longitude": session.base_gps.get("longitude"),
        "base_accuracy_m": session.base_gps.get("accuracy"),
        "current_latitude": session.current_gps.get("latitude"),
        "current_longitude": session.current_gps.get("longitude"),
        "current_accuracy_m": session.current_gps.get("accuracy"),
        "horizontal_distance_from_tree_m": derived.get("horizontal_distance_from_tree_m"),
        "distance_reliability_status": derived.get("distance_reliability_status"),
        "gps_accuracy_status": derived.get("gps_accuracy_status"),
        "gps_quality_reason": derived.get("gps_quality_reason"),
        "foreground_recording_status": "FOREGROUND_RECORDING_REQUIRED",
        "manual_input_status": _LATEST_MANUAL_INPUT.get("manual_input_status", ""),
        "page_source": page_source,
        "result_page_url": f"/field-result?session_id={session.session_id}",
        "report_page_url": f"/field-report?session_id={session.session_id}",
    }


def _get_or_latest(session_id: Any | None = None, *, create_if_missing: bool = False) -> FieldSession:
    key = str(session_id or _LATEST_SESSION_ID or "")
    if key and key in _SESSIONS:
        return _SESSIONS[key]
    if not create_if_missing and key:
        raise KeyError(f"Field session not found: {key}")
    payload = {"session_id": key or f"FS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"}
    start_field_session(payload)
    return _SESSIONS[payload["session_id"]]


def _save_session(session: FieldSession, *, runtime_root: Path | None = None) -> None:
    root = (runtime_root / "field_sessions") if runtime_root else SESSION_RUNTIME_DIR
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{session.session_id}.json").write_text(json.dumps(asdict(session), indent=2, ensure_ascii=False), encoding="utf-8")


def _base_result(model_status: str) -> dict[str, Any]:
    return {
        "status": "MODEL_NOT_READY_NO_FAKE_DETECTION" if model_status == "MODEL_NOT_READY" else "FIELD_RESULT_PROVISIONAL",
        "model_status": model_status,
        "geometry_status": "INSUFFICIENT_GEOMETRY_DATA",
        "reason_codes": ["MODEL_NOT_READY_NO_FAKE_DETECTION" if model_status == "MODEL_NOT_READY" else "FIELD_RESULT_PROVISIONAL"],
    }


def _basic_map_html(lat: Any, lon: Any, point_id: str) -> str:
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><title>Field Session Map</title></head>
<body><h1>Field Session Map</h1><p>Status: MAP_BASIC_FALLBACK</p>
<p>Point: {html.escape(point_id)}</p><p>Latitude: {lat}</p><p>Longitude: {lon}</p>
</body></html>"""


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
