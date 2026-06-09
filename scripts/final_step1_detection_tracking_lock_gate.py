from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

ROOT = Path(r"E:\Projects\ULP_Project")
SRC = ROOT / "src"
REPORT = ROOT / "reports" / "final_step1_detection_tracking_lock_gate.json"

sys.path.insert(0, str(SRC))


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_app():
    mod = importlib.import_module("ulp_project.flask_app")
    if hasattr(mod, "create_app"):
        return mod.create_app()
    if hasattr(mod, "app"):
        return mod.app
    if hasattr(mod, "get_app"):
        return mod.get_app()
    raise RuntimeError("APP_FACTORY_NOT_FOUND")


def route_set(app) -> set[str]:
    return {rule.rule for rule in app.url_map.iter_rules()}


def post_json(client, path: str, payload: Dict[str, Any]):
    resp = client.post(path, json=payload)
    data = resp.get_json(silent=True)
    if data is None:
        data = resp.get_data(as_text=True)[:800]
    return resp.status_code, data


def get_text(client, path: str):
    resp = client.get(path)
    raw = resp.get_data()
    if isinstance(raw, bytes):
        body = raw.decode("utf-8", errors="ignore")
    else:
        body = str(raw)
    return resp.status_code, body


def make_jpeg_data_url() -> str:
    import base64
    import cv2
    import numpy as np

    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (18, 18, 18)
    cv2.rectangle(img, (210, 80), (430, 400), (20, 170, 70), -1)
    cv2.rectangle(img, (210, 80), (430, 400), (190, 255, 210), 3)
    cv2.putText(img, "STEP1 DETECTION TRACKING", (95, 445), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (230, 255, 235), 2)
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 84])
    if not ok:
        raise RuntimeError("JPEG_ENCODE_FAILED")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def main() -> int:
    result: Dict[str, Any] = {
        "version": "final_step1_detection_tracking_lock_gate",
        "timestamp": now(),
        "root": str(ROOT),
        "status": "UNKNOWN",
        "hard_failures": [],
        "warnings": [],
        "route_checks": {},
        "ui_checks": {},
        "request_checks": {},
        "policy": {
            "step_name": "LANGKAH_BESAR_1_DETEKSI_REALTIME_TRACKING",
            "realtime_core": "/api/field/session/frame",
            "camera_page": "/field-camera?session_id=<session_id>",
            "cloud_vision_policy": "OPTIONAL_VALIDATOR_ONLY_NOT_REALTIME_CORE",
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
            "no_fake_detection": True,
            "no_fake_gps": True,
            "no_fake_clearance": True,
        },
    }

    app = load_app()
    client = app.test_client()
    routes = route_set(app)

    required_routes = [
        "/field-capture",
        "/field-camera",
        "/api/field/session/start",
        "/api/field/session/frame",
        "/api/field/session/gps-update",
        "/api/field/session/shutter",
        "/api/field/session/vision-analyze",
        "/api/field/session/progress6-28-diagnostic-frame",
        "/field-map/session/<session_id>",
        "/field-spreadsheet/session/<session_id>",
    ]

    result["route_checks"] = {route: route in routes for route in required_routes}
    missing_routes = [route for route in required_routes if route not in routes]
    if missing_routes:
        result["hard_failures"].append({"missing_routes": missing_routes})

    status_capture, html_capture = get_text(client, "/field-capture")
    result["ui_checks"]["field_capture_http_status"] = status_capture
    result["ui_checks"]["field_capture_has_title"] = "Monitoring Vegetasi 20 kV" in html_capture or "Field Capture" in html_capture
    if status_capture in (404, 405, 500):
        result["hard_failures"].append({"field_capture_bad_http": status_capture})

    status_camera_empty, html_camera_empty = get_text(client, "/field-camera")
    result["ui_checks"]["field_camera_empty_http_status"] = status_camera_empty
    result["ui_checks"]["field_camera_handles_missing_session"] = "FIELD_SESSION_ID_REQUIRED" in html_camera_empty or status_camera_empty in (200, 400)
    if status_camera_empty in (404, 405, 500):
        result["hard_failures"].append({"field_camera_empty_bad_http": status_camera_empty})

    start_payload = {
        "point_id": "V001_pohon_sono",
        "operator_name": "step1_lock",
        "notes": "final_step1_detection_tracking_lock",
        "secure_context_status": "SECURE_CONTEXT_OK",
        "current_url_mode": "HTTPS_PUBLIC_READY",
        "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
        "camera_status": "CAMERA_READY",
        "gps_status": "GPS_READY",
        "gps_source": "GPS_SOURCE_BROWSER",
        "base_latitude": -7.2161234,
        "base_longitude": 112.7351234,
        "base_accuracy_m": 3.8,
    }

    start_status, start_data = post_json(client, "/api/field/session/start", start_payload)
    result["request_checks"]["session_start"] = {"http_status": start_status, "data": start_data}

    if start_status not in (200, 201):
        result["hard_failures"].append({"session_start_bad_http": start_status})

    session_id = ""
    if isinstance(start_data, dict):
        session_id = str(start_data.get("session_id") or "")
        camera_url = str(start_data.get("camera_url") or "")
        if not session_id:
            result["hard_failures"].append("SESSION_ID_EMPTY")
        if session_id and session_id not in camera_url:
            result["hard_failures"].append("CAMERA_URL_MISSING_SESSION_ID")
        if start_data.get("no_fake_detection") is not True:
            result["warnings"].append("SESSION_START_NO_FAKE_DETECTION_FLAG_NOT_TRUE")
    else:
        result["hard_failures"].append("SESSION_START_NON_JSON_RESPONSE")

    if not session_id:
        session_id = "FS_FINAL_STEP1_FALLBACK"

    status_camera_session, html_camera_session = get_text(client, f"/field-camera?session_id={session_id}")
    result["ui_checks"]["field_camera_session_http_status"] = status_camera_session
    result["ui_checks"]["field_camera_has_video"] = "<video" in html_camera_session
    result["ui_checks"]["field_camera_has_session_id"] = session_id in html_camera_session or "session_id" in html_camera_session
    result["ui_checks"]["field_camera_mentions_yolo_lock"] = "progress6_27_yolo_first_lock.js" in html_camera_session or "YOLO-FIRST" in html_camera_session

    if status_camera_session in (404, 405, 500):
        result["hard_failures"].append({"field_camera_session_bad_http": status_camera_session})
    if "<video" not in html_camera_session:
        result["hard_failures"].append("FIELD_CAMERA_VIDEO_ELEMENT_MISSING")

    frame_data_url = make_jpeg_data_url()

    frame_payload = {
        "session_id": session_id,
        "frame_base64": frame_data_url,
        "image_base64": frame_data_url,
        "source": "final_step1_detection_tracking_lock",
        "realtime_mode": "YOLO_FIRST",
        "no_fake_detection": True,
        "synthetic_smoke": True,
    }

    frame_status, frame_data = post_json(client, "/api/field/session/frame", frame_payload)
    result["request_checks"]["session_frame"] = {"http_status": frame_status, "data": frame_data}

    if frame_status in (404, 405, 500):
        result["hard_failures"].append({"session_frame_bad_http": frame_status})

    if isinstance(frame_data, dict):
        if frame_data.get("no_fake_detection") is not True:
            result["hard_failures"].append("FRAME_NO_FAKE_DETECTION_NOT_TRUE")
        runtime_mode = str(frame_data.get("runtime_mode") or "")
        if runtime_mode and "YOLO" not in runtime_mode:
            result["warnings"].append({"frame_runtime_mode_not_yolo_explicit": runtime_mode})
    else:
        result["warnings"].append("FRAME_RESPONSE_NON_JSON")

    diag_status, diag_data = post_json(
        client,
        "/api/field/session/progress6-28-diagnostic-frame",
        {
            "session_id": session_id,
            "frame_base64": frame_data_url,
            "synthetic_smoke": True,
            "source": "final_step1_tracking_diagnostic",
        },
    )
    result["request_checks"]["tracking_diagnostic"] = {"http_status": diag_status, "data": diag_data}

    if diag_status in (404, 405, 500):
        result["hard_failures"].append({"tracking_diagnostic_bad_http": diag_status})

    if isinstance(diag_data, dict):
        tracking = diag_data.get("tracking", {})
        measurement = diag_data.get("measurement", {})
        if tracking.get("track_id_seen") is not True:
            result["hard_failures"].append("TRACK_ID_NOT_SEEN_IN_DIAGNOSTIC")
        if measurement.get("clearance_status") not in {"CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR", "CLEARANCE_NOT_FINAL"}:
            result["hard_failures"].append("CLEARANCE_GUARD_NOT_SAFE")
        if measurement.get("eta_status") not in {"ETA_NOT_FINAL", "INSUFFICIENT_GEOMETRY_DATA"}:
            result["hard_failures"].append("ETA_GUARD_NOT_SAFE")
        if diag_data.get("no_fake_detection") is not True:
            result["hard_failures"].append("DIAGNOSTIC_NO_FAKE_DETECTION_NOT_TRUE")
    else:
        result["hard_failures"].append("TRACKING_DIAGNOSTIC_NON_JSON")

    vision_status, vision_data = post_json(
        client,
        "/api/field/session/vision-analyze",
        {
            "session_id": session_id,
            "image_base64": frame_data_url,
            "source": "final_step1_optional_validator_probe",
            "no_fake_detection": True,
        },
    )
    result["request_checks"]["vision_analyze_optional"] = {
        "http_status": vision_status,
        "policy": "MUST_NOT_BE_REALTIME_CORE",
        "data_preview": vision_data if isinstance(vision_data, dict) else str(vision_data)[:500],
    }

    if vision_status in (404, 405, 500):
        result["warnings"].append({"vision_analyze_optional_bad_http": vision_status})

    shutter_status, shutter_data = post_json(
        client,
        "/api/field/session/shutter",
        {
            "session_id": session_id,
            "idempotency_key": "final_step1_lock_once",
            "camera_status": "CAMERA_READY",
            "model_status": "TREE_MODEL_READY_CANDIDATE",
            "no_fake_detection": True,
            "no_fake_gps": True,
        },
    )
    result["request_checks"]["shutter_evidence"] = {"http_status": shutter_status, "data": shutter_data}

    if shutter_status in (404, 405, 500):
        result["hard_failures"].append({"shutter_bad_http": shutter_status})

    if result["hard_failures"]:
        result["status"] = "DETECTION_TRACKING_FIELD_CAMERA_LOCK_FAILED"
        code = 1
    else:
        result["status"] = "DETECTION_TRACKING_FIELD_CAMERA_LOCKED"
        code = 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
