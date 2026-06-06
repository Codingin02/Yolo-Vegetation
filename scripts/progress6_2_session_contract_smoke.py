from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        client = create_app(runtime_root=Path(tmp)).test_client()
        start = client.post(
            "/api/field/session/start",
            json={
                "session_id": "SMOKE_NATIVE_GPS_SESSION",
                "point_id": "V001_pohon_sono",
                "operator_name": "operator-smoke",
                "secure_context_status": "SECURE_CONTEXT_OK",
                "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
                "camera_status": "CAMERA_READY",
                "base_gps": {
                    "latitude": -7.1,
                    "longitude": 112.7,
                    "accuracy": 8,
                    "source": "GPS_SOURCE_BROWSER",
                },
            },
        ).get_json()
        session_id = start["session_id"]
        gps = client.post(
            "/api/field/session/gps-update",
            json={
                "session_id": session_id,
                "latitude": -7.1002,
                "longitude": 112.7,
                "accuracy": 8,
                "source": "GPS_SOURCE_BROWSER",
            },
        ).get_json()
        frame = client.post("/api/field/session/frame", json={"session_id": session_id}).get_json()
        report = client.post(
            "/api/field/session/shutter",
            json={"session_id": session_id, "notes": "session smoke"},
        ).get_json()
        stop = client.post("/api/field/session/stop", json={"session_id": session_id}).get_json()

    checks = {
        "start_active": start["session_status"] == "RECORDING_ACTIVE",
        "gps_browser_source": gps["gps"]["source"] == "GPS_SOURCE_BROWSER",
        "frame_no_fake_detection": frame.get("no_fake_detection") is True,
        "frame_model_not_ready_no_fake": frame.get("model_status") == "MODEL_NOT_READY" and frame.get("detections") == [],
        "report_written": report["status"] in {"FIELD_SESSION_REPORT_WRITTEN", "FIELD_SESSION_SHUTTER_SAVED"},
        "stop_recording_stopped": stop["session_status"] == "RECORDING_STOPPED",
    }
    status = "PROGRESS_6_2_SESSION_CONTRACT_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_2_SESSION_CONTRACT_SMOKE_FAIL"
    return {"status": status, "checks": checks, "session_id": session_id}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
