from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(r"E:\Projects\ULP_Project")
SRC = ROOT / "src"
REPORT = ROOT / "reports" / "progress6_29_field_acceptance_gate.json"

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


def safe_get_json(client, path: str):
    resp = client.get(path)
    try:
        data = resp.get_json(silent=True)
    except Exception:
        data = None
    if data is None:
        data = resp.get_data(as_text=True)[:600]
    return resp.status_code, data


def safe_post_json(client, path: str, payload: Dict[str, Any]):
    resp = client.post(path, json=payload)
    try:
        data = resp.get_json(silent=True)
    except Exception:
        data = None
    if data is None:
        data = resp.get_data(as_text=True)[:600]
    return resp.status_code, data


def route_set(app) -> set[str]:
    return {rule.rule for rule in app.url_map.iter_rules()}


def make_jpeg_data_url() -> str:
    import base64
    import cv2
    import numpy as np

    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (18, 18, 18)
    cv2.rectangle(img, (210, 80), (430, 400), (20, 170, 70), -1)
    cv2.rectangle(img, (210, 80), (430, 400), (190, 255, 210), 3)
    cv2.putText(img, "FIELD ACCEPTANCE SYNTHETIC", (95, 445), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (230, 255, 235), 2)
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 84])
    if not ok:
        raise RuntimeError("JPEG_ENCODE_FAILED")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def main() -> int:
    result: Dict[str, Any] = {
        "version": "progress6_29_field_acceptance_gate",
        "timestamp": now(),
        "root": str(ROOT),
        "status": "UNKNOWN",
        "hard_failures": [],
        "warnings": [],
        "acceptance": {},
        "route_checks": {},
        "request_checks": {},
        "final_report_freeze": {},
        "safety": {
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

    required_files = [
        ROOT / "docs" / "PROGRESS_6_27_TO_6_29_FINAL_ROUTE.md",
        ROOT / "docs" / "PROGRESS_6_28_TRACKING_MEASUREMENT_OUTPUT.md",
        ROOT / "scripts" / "progress6_27_yolo_first_route_smoke.py",
        ROOT / "scripts" / "progress6_28_tracking_measurement_smoke.py",
        ROOT / "src" / "ulp_project" / "static" / "progress6_27_yolo_first_lock.js",
        ROOT / "src" / "ulp_project" / "progress6_28_tracking_measurement_runtime.py",
    ]

    result["acceptance"]["required_files"] = {str(p.relative_to(ROOT)): p.exists() for p in required_files}
    missing_files = [str(p.relative_to(ROOT)) for p in required_files if not p.exists()]
    if missing_files:
        result["hard_failures"].append({"missing_required_files": missing_files})

    app = load_app()
    client = app.test_client()
    routes = route_set(app)

    required_routes = [
        "/field-capture",
        "/field-camera",
        "/field-map/session/<session_id>",
        "/field-spreadsheet/session/<session_id>",
        "/api/field/session/start",
        "/api/field/session/frame",
        "/api/field/session/gps-update",
        "/api/field/session/shutter",
        "/api/field/session/vision-analyze",
        "/api/field/session/progress6-28-diagnostic-frame",
    ]

    result["route_checks"] = {r: (r in routes) for r in required_routes}
    missing_routes = [r for r in required_routes if r not in routes]
    if missing_routes:
        result["hard_failures"].append({"missing_routes": missing_routes})

    # UI entry smoke.
    for path in ["/field-capture"]:
        status, data = safe_get_json(client, path)
        result["request_checks"][path] = {
            "http_status": status,
            "data_preview": str(data)[:500],
        }
        if status in (404, 405, 500):
            result["hard_failures"].append({f"bad_http_{path}": status})

    # Session flow smoke.
    start_payload = {
        "point_id": "V001_pohon_sono",
        "operator_name": "field_acceptance_smoke",
        "notes": "progress6_29_acceptance",
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

    start_status, start_data = safe_post_json(client, "/api/field/session/start", start_payload)
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
            result["hard_failures"].append("CAMERA_URL_DOES_NOT_CONTAIN_SESSION_ID")
        if start_data.get("no_fake_detection") is not True:
            result["warnings"].append("session_start_no_fake_detection_flag_missing")
    else:
        result["hard_failures"].append("SESSION_START_NON_JSON")

    if not session_id:
        session_id = "FS_PROGRESS6_29_FALLBACK"

    frame_data = make_jpeg_data_url()

    frame_payload = {
        "session_id": session_id,
        "frame_base64": frame_data,
        "image_base64": frame_data,
        "source": "progress6_29_field_acceptance_synthetic",
        "realtime_mode": "YOLO_FIRST",
        "no_fake_detection": True,
        "synthetic_smoke": True,
    }

    frame_status, frame_response = safe_post_json(client, "/api/field/session/frame", frame_payload)
    result["request_checks"]["session_frame"] = {"http_status": frame_status, "data": frame_response}
    if frame_status in (404, 405, 500):
        result["hard_failures"].append({"session_frame_bad_http": frame_status})
    if isinstance(frame_response, dict):
        if frame_response.get("runtime_mode") not in {"YOLO_FIRST", "YOLO_FIRST_TRACKING_MEASUREMENT_DIAGNOSTIC"}:
            result["warnings"].append("FRAME_RUNTIME_MODE_NOT_EXPLICIT_YOLO_FIRST")
        if frame_response.get("no_fake_detection") is not True:
            result["hard_failures"].append("FRAME_NO_FAKE_DETECTION_FLAG_FALSE_OR_MISSING")

    gps_payload = {
        "session_id": session_id,
        "latitude": -7.2161234,
        "longitude": 112.7351234,
        "accuracy_m": 3.8,
        "gps_source": "GPS_SOURCE_BROWSER",
        "no_fake_gps": True,
    }

    gps_status, gps_response = safe_post_json(client, "/api/field/session/gps-update", gps_payload)
    result["request_checks"]["gps_update"] = {"http_status": gps_status, "data": gps_response}
    if gps_status in (404, 405, 500):
        result["hard_failures"].append({"gps_update_bad_http": gps_status})

    diag_status, diag_response = safe_post_json(
        client,
        "/api/field/session/progress6-28-diagnostic-frame",
        {
            "session_id": session_id,
            "frame_base64": frame_data,
            "synthetic_smoke": True,
        },
    )
    result["request_checks"]["progress6_28_diagnostic_frame"] = {"http_status": diag_status, "data": diag_response}
    if diag_status in (404, 405, 500):
        result["hard_failures"].append({"progress6_28_diagnostic_bad_http": diag_status})
    if isinstance(diag_response, dict):
        measurement = diag_response.get("measurement", {})
        if measurement.get("clearance_status") != "CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR":
            result["hard_failures"].append("CLEARANCE_GUARD_NOT_LOCKED")
        if measurement.get("eta_status") != "ETA_NOT_FINAL":
            result["hard_failures"].append("ETA_GUARD_NOT_LOCKED")
        tracking = diag_response.get("tracking", {})
        if tracking.get("track_id_seen") is not True:
            result["hard_failures"].append("TRACKING_ID_NOT_SEEN_ON_SYNTHETIC_ACCEPTANCE")

    shutter_payload = {
        "session_id": session_id,
        "idempotency_key": "progress6_29_acceptance_once",
        "camera_status": "CAMERA_READY",
        "model_status": "TREE_MODEL_READY_CANDIDATE",
        "gps": gps_payload,
        "no_fake_detection": True,
        "no_fake_gps": True,
    }

    shutter_status, shutter_response = safe_post_json(client, "/api/field/session/shutter", shutter_payload)
    result["request_checks"]["shutter"] = {"http_status": shutter_status, "data": shutter_response}
    if shutter_status in (404, 405, 500):
        result["hard_failures"].append({"shutter_bad_http": shutter_status})
    if isinstance(shutter_response, dict):
        if shutter_response.get("map_status") != "MAP_HTML_READY":
            result["hard_failures"].append("MAP_NOT_READY_AFTER_SHUTTER")
        if shutter_response.get("result_status") != "SPREADSHEET_READY":
            result["hard_failures"].append("SPREADSHEET_NOT_READY_AFTER_SHUTTER")
        if shutter_response.get("no_fake_detection") is not True:
            result["hard_failures"].append("SHUTTER_NO_FAKE_DETECTION_FLAG_FALSE_OR_MISSING")
        if shutter_response.get("no_fake_gps") is not True:
            result["hard_failures"].append("SHUTTER_NO_FAKE_GPS_FLAG_FALSE_OR_MISSING")

    map_status, map_response = safe_get_json(client, f"/field-map/session/{session_id}")
    result["request_checks"]["map"] = {"http_status": map_status, "data_preview": str(map_response)[:500]}
    if map_status in (404, 405, 500):
        result["hard_failures"].append({"map_bad_http": map_status})

    sheet_status, sheet_response = safe_get_json(client, f"/field-spreadsheet/session/{session_id}")
    result["request_checks"]["spreadsheet"] = {"http_status": sheet_status, "data_preview": str(sheet_response)[:500]}
    if sheet_status in (404, 405, 500):
        result["hard_failures"].append({"spreadsheet_bad_http": sheet_status})

    result["final_report_freeze"] = {
        "system_claim": "Prototype sistem monitoring vegetasi jaringan distribusi 20 kV berbasis HP browser, Flask, HTTPS tunnel, YOLO-first candidate runtime, GPS evidence, map evidence, dan spreadsheet-ready output.",
        "must_claim": [
            "Sistem field-capture berbasis HP browser dan backend laptop telah siap untuk field-trial terbatas.",
            "YOLO-first runtime route telah dikunci sebagai core realtime.",
            "Tracking diagnostic dan edge diagnostic telah tersedia untuk bukti teknis runtime.",
            "Map dan spreadsheet output tersedia setelah shutter.",
            "Safety guard no fake detection, no fake GPS, no fake clearance aktif.",
        ],
        "must_not_claim": [
            "Bukan sistem produksi final PLN.",
            "Bukan clearance final karena pole/conductor/reference geometry belum final.",
            "Bukan ETA pemangkasan final karena clearance final belum tersedia.",
            "Bukan pertumbuhan biologis final karena growth model masih proxy.",
            "Bukan multi-class final karena conductor/pole model belum siap.",
            "Cloud vision bukan core realtime.",
        ],
        "report_wording_status": "READY_FOR_FINAL_REPORT_AS_LIMITED_FIELD_TRIAL_PROTOTYPE",
    }

    result["acceptance"]["field_acceptance_status"] = (
        "FIELD_ACCEPTANCE_READY_LIMITED_TRIAL"
        if not result["hard_failures"]
        else "FIELD_ACCEPTANCE_NOT_READY"
    )

    if result["hard_failures"]:
        result["status"] = "PROGRESS_6_29_FIELD_ACCEPTANCE_FAILED"
        code = 1
    else:
        result["status"] = "PROGRESS_6_29_FIELD_ACCEPTANCE_PASS"
        code = 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
