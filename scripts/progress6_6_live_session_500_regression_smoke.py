from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def run_smoke() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        client = create_app(runtime_root=Path(tmp)).test_client()
        start_payload = {
            "point_id": "V001_pohon_sono",
            "operator_name": "",
            "notes": "",
            "secure_context_status": "SECURE_CONTEXT_OK",
            "current_url_mode": "HTTPS_PUBLIC_READY",
            "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
            "camera_status": "CAMERA_READY",
            "gps_status": "GPS_READY",
            "gps_source": "GPS_SOURCE_BROWSER",
            "base_latitude": -7.2161234,
            "base_longitude": 112.7351234,
            "base_accuracy_m": 3.8,
            "source_mode": "SMOKE_TEST",
        }
        start = client.post("/api/field/session/start", json=start_payload)
        start_json = start.get_json() or {}
        session_id = start_json.get("session_id")
        shutter_payload = {
            "session_id": session_id,
            "idempotency_key": "P66_LIVE_HP_PAYLOAD",
            "point_id": "V001_pohon_sono",
            "camera_status": "CAMERA_READY",
            "model_status": "MODEL_NOT_READY",
            "gps_source": "GPS_SOURCE_BROWSER",
            "current_latitude": -7.2161288,
            "current_longitude": 112.7351288,
            "current_accuracy_m": 6.7,
            "source_mode": "SMOKE_TEST",
        }
        shutter = client.post("/api/field/session/shutter", json=shutter_payload)
        duplicate = client.post("/api/field/session/shutter", json=shutter_payload)
        stop = client.post("/api/field/session/stop", json={"session_id": session_id})
        shutter_json = shutter.get_json() or {}
        duplicate_json = duplicate.get_json() or {}
        checks = {
            "start_no_500": start.status_code != 500,
            "start_has_session": bool(session_id),
            "start_gps_precision": start_json.get("gps", {}).get("base", {}).get("latitude_raw") == "-7.2161234",
            "shutter_no_500": shutter.status_code != 500,
            "shutter_saved": shutter_json.get("status") == "FIELD_SESSION_SHUTTER_SAVED",
            "shutter_current_precision": shutter_json.get("current_latitude_raw") == "-7.2161288",
            "duplicate_ignored": (duplicate_json.get("status") == "DUPLICATE_SHUTTER_IGNORED" and duplicate_json.get("csv_appended") is False),
            "stop_no_500": stop.status_code != 500,
            "stop_stopped": (stop.get_json() or {}).get("status") == "FIELD_SESSION_STOPPED",
            "model_not_ready_safe": shutter_json.get("no_fake_detection") is True,
        }
    return {
        "status": "PROGRESS_6_6_LIVE_SESSION_ROUTES_NO_500_PASS" if all(checks.values()) else "PROGRESS_6_6_LIVE_SESSION_ROUTES_NO_500_FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
