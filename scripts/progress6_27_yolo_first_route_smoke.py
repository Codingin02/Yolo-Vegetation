from __future__ import annotations

import base64
import importlib
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(r"E:\Projects\ULP_Project")
SRC = ROOT / "src"
REPORT = ROOT / "reports" / "progress6_27_yolo_first_route_smoke.json"

sys.path.insert(0, str(SRC))

REQUIRED_ROUTES = [
    "/field-capture",
    "/field-camera",
    "/field-map/session/<session_id>",
    "/field-spreadsheet/session/<session_id>",
    "/api/field/session/start",
    "/api/field/session/frame",
    "/api/field/session/gps-update",
    "/api/field/session/shutter",
    "/api/field/session/vision-analyze",
]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def make_valid_jpeg_data_url() -> str:
    """
    Membuat JPEG valid menggunakan OpenCV + NumPy agar smoke tidak lagi
    memunculkan libpng CRC error. Ini hanya synthetic diagnostic frame,
    bukan data lapangan dan bukan fake detection.
    """
    import cv2
    import numpy as np

    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (35, 55, 45)
    cv2.rectangle(img, (180, 80), (460, 410), (45, 120, 70), 3)
    cv2.putText(
        img,
        "PROGRESS_6_27_SMOKE",
        (120, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (220, 255, 230),
        2,
        cv2.LINE_AA,
    )

    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    if not ok:
        raise RuntimeError("JPEG_ENCODE_FAILED")

    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def load_app():
    mod = importlib.import_module("ulp_project.flask_app")

    if hasattr(mod, "create_app"):
        return mod.create_app()

    if hasattr(mod, "app"):
        return mod.app

    if hasattr(mod, "get_app"):
        return mod.get_app()

    raise RuntimeError("Tidak menemukan create_app/app/get_app di ulp_project.flask_app")


def route_set(app) -> set[str]:
    return {rule.rule for rule in app.url_map.iter_rules()}


def request_json(client, method: str, path: str, payload: Dict[str, Any] | None = None) -> Tuple[int, Dict[str, Any] | str]:
    try:
        if method == "GET":
            resp = client.get(path)
        else:
            resp = client.post(path, json=payload or {})

        status = resp.status_code

        try:
            data = resp.get_json(silent=True)
            if data is not None:
                return status, data
        except Exception:
            pass

        return status, resp.get_data(as_text=True)[:500]

    except Exception as exc:
        return 599, {
            "exception": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }


def main() -> int:
    result: Dict[str, Any] = {
        "version": "progress6_27_yolo_first_route_smoke",
        "timestamp": now(),
        "root": str(ROOT),
        "status": "UNKNOWN",
        "hard_failures": [],
        "warnings": [],
        "route_checks": {},
        "request_checks": {},
        "policy": {
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
            "realtime_core": "/api/field/session/frame",
            "cloud_vision_policy": "validator_or_review_only",
            "shutter_policy": "evidence_only",
            "synthetic_frame_only": True,
        },
    }

    try:
        app = load_app()
        routes = route_set(app)
        result["routes_seen_count"] = len(routes)
        result["route_checks"] = {r: (r in routes) for r in REQUIRED_ROUTES}

        missing = [r for r in REQUIRED_ROUTES if r not in routes]
        if missing:
            result["hard_failures"].append({"missing_routes": missing})

        client = app.test_client()

        start_payload = {
            "point_id": "V001_pohon_sono",
            "operator_name": "",
            "notes": "progress6_27_smoke",
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

        start_status, start_data = request_json(client, "POST", "/api/field/session/start", start_payload)
        result["request_checks"]["session_start"] = {"http_status": start_status, "data": start_data}

        if start_status in (404, 405, 500, 599):
            result["hard_failures"].append({"session_start_bad_status": start_status})

        session_id = ""
        if isinstance(start_data, dict):
            session_id = str(start_data.get("session_id") or "")
            camera_url = str(start_data.get("camera_url") or "")

            if not session_id:
                result["hard_failures"].append("session_start_no_session_id")

            if session_id.startswith("FS_DEGRADED"):
                result["hard_failures"].append("session_start_degraded_session_id")

            if session_id and session_id not in camera_url:
                result["hard_failures"].append("camera_url_missing_session_id")
        else:
            result["hard_failures"].append("session_start_non_json_response")

        if not session_id:
            session_id = "FS_PROGRESS6_27_SMOKE_FALLBACK"

        frame_data_url = make_valid_jpeg_data_url()

        frame_payload = {
            "session_id": session_id,
            "frame_base64": frame_data_url,
            "image_base64": frame_data_url,
            "source": "progress6_27_smoke_valid_jpeg",
            "realtime_mode": "YOLO_FIRST",
            "no_fake_detection": True,
            "shutter_triggered": False,
        }

        frame_status, frame_data = request_json(client, "POST", "/api/field/session/frame", frame_payload)
        result["request_checks"]["session_frame"] = {"http_status": frame_status, "data": frame_data}

        if frame_status in (404, 405, 500, 599):
            result["hard_failures"].append({"session_frame_bad_status": frame_status})

        gps_payload = {
            "session_id": session_id,
            "latitude": -7.2161234,
            "longitude": 112.7351234,
            "accuracy_m": 3.8,
            "gps_source": "GPS_SOURCE_BROWSER",
            "no_fake_gps": True,
        }

        gps_status, gps_data = request_json(client, "POST", "/api/field/session/gps-update", gps_payload)
        result["request_checks"]["gps_update"] = {"http_status": gps_status, "data": gps_data}

        if gps_status in (404, 405, 500, 599):
            result["hard_failures"].append({"gps_update_bad_status": gps_status})

        shutter_payload = {
            "session_id": session_id,
            "idempotency_key": "progress6_27_smoke_once",
            "camera_status": "CAMERA_READY",
            "model_status": "MODEL_NOT_READY_OR_CANDIDATE",
            "gps": gps_payload,
            "no_fake_detection": True,
            "no_fake_gps": True,
        }

        shutter_status, shutter_data = request_json(client, "POST", "/api/field/session/shutter", shutter_payload)
        result["request_checks"]["shutter"] = {"http_status": shutter_status, "data": shutter_data}

        if shutter_status in (404, 405, 500, 599):
            result["hard_failures"].append({"shutter_bad_status": shutter_status})

        map_status, map_data = request_json(client, "GET", f"/field-map/session/{session_id}")
        result["request_checks"]["map"] = {"http_status": map_status, "data_preview": str(map_data)[:300]}

        if map_status in (404, 405, 500, 599):
            result["hard_failures"].append({"map_bad_status": map_status})

        sheet_status, sheet_data = request_json(client, "GET", f"/field-spreadsheet/session/{session_id}")
        result["request_checks"]["spreadsheet"] = {"http_status": sheet_status, "data_preview": str(sheet_data)[:300]}

        if sheet_status in (404, 405, 500, 599):
            result["hard_failures"].append({"spreadsheet_bad_status": sheet_status})

        if result["hard_failures"]:
            result["status"] = "PROGRESS_6_27_YOLO_FIRST_ROUTE_SMOKE_FAILED"
            exit_code = 1
        else:
            result["status"] = "PROGRESS_6_27_YOLO_FIRST_ROUTE_SMOKE_PASS"
            exit_code = 0

    except Exception as exc:
        result["status"] = "PROGRESS_6_27_YOLO_FIRST_ROUTE_SMOKE_EXCEPTION"
        result["hard_failures"].append({
            "exception": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        })
        exit_code = 1

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
