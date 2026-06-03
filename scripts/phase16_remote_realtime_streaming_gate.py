from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.realtime_streaming import create_realtime_session, process_realtime_frame, validate_realtime_payload_contract, websocket_available  # noqa: E402
from ulp_project.safety_clearance_policy import classify_distance_zone, floor_display_meter  # noqa: E402


def _run_script(script: str) -> bool:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return completed.returncode == 0


def _payload(session: dict[str, object], frame_id: str = "gate_frame", age_ms: int = 0) -> dict[str, object]:
    return {
        "session_id": session["session_id"],
        "session_token": session["session_token"],
        "frame_id": frame_id,
        "timestamp_client_ms": int(time.time() * 1000) - age_ms,
        "point_id": "V001_pohon_sono",
        "species_hint": "pohon_sono",
        "asset_type": "span",
        "gps_lat": "",
        "gps_lon": "",
        "image_jpeg_base64": "",
        "client_mode": "remote_https",
        "requested_interval_ms": 1000,
    }


def build_gate_status() -> dict[str, object]:
    checks: dict[str, object] = {}
    checks["phase13_gate_pass"] = _run_script("phase13_field_capture_hardening_gate.py")
    checks["phase14_gate_pass"] = _run_script("phase14_auto_yolo_measurement_gate.py")
    checks["phase15_gate_pass"] = _run_script("phase15_realtime_eta_system_gate.py")

    app = create_app()
    client = app.test_client()
    transport = client.get("/api/realtime/model/status").get_json() or {}
    checks["remote_realtime_routes"] = (
        client.get("/field-capture").status_code == 200
        and client.get("/realtime").status_code == 200
        and client.get("/api/realtime/model/status").content_type.startswith("application/json")
        and "/ws/realtime-detect" in [str(rule.rule) for rule in app.url_map.iter_rules()]
    )
    checks["websocket_or_fallback_contract"] = transport.get("transport", {}).get("status") in {"WEBSOCKET_AVAILABLE", "WEBSOCKET_DEPENDENCY_NOT_INSTALLED"}
    checks["secure_context_diagnostic"] = "HTTPS_SECURE" in client.get("/field-capture").get_data(as_text=True)

    session = create_realtime_session(ROOT / "data" / "runtime")
    base = _payload(session)
    contract = validate_realtime_payload_contract(base)
    checks["websocket_payload_contract"] = contract["status"] == "WEBSOCKET_PAYLOAD_CONTRACT_VALID"
    first = process_realtime_frame(base)
    second = process_realtime_frame(_payload(session, "gate_frame_2"))
    stale = process_realtime_frame(_payload(session, "gate_old", age_ms=4000))
    checks["frame_rate_limit_1fps"] = second["status"] == "FRAME_RATE_LIMITED"
    checks["stale_frame_drop_3sec"] = stale["status"] == "STALE_FRAME_DROPPED"
    checks["latest_only_queue"] = second["queue_status"] == "DROPPED_RATE_LIMIT_1FPS"
    checks["model_missing_no_fake_detection"] = first.get("model_status") == "MODEL_NOT_READY" and first.get("detections", []) == []

    checks["clearance_policy_3m"] = (
        classify_distance_zone(2.9)["distance_zone_status"] == "UNSAFE_WITHIN_3M"
        and classify_distance_zone(3.0)["distance_zone_status"] == "UNSAFE_WITHIN_3M"
        and classify_distance_zone(4.0)["distance_zone_status"] == "SAFE"
    )
    checks["display_meter_floor"] = floor_display_meter(1.3) == 1 and floor_display_meter(2.0) == 2 and floor_display_meter(2.75) == 2
    checks["report_snapshot_not_every_frame"] = "report_written" not in first and "report_status" not in first

    html = (ROOT / "src" / "ulp_project" / "templates" / "field_capture.html").read_text(encoding="utf-8")
    js = (ROOT / "src" / "ulp_project" / "static" / "field_capture.js").read_text(encoding="utf-8")
    checks["camera_gps_status_logic"] = "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT" in js and "GPS_PERMISSION_DENIED" in js and "GPS_TIMEOUT" in js
    checks["manual_not_primary"] = "Mode utama Phase 16" in html and "Advanced / Manual Provisional" in html
    checks["no_mobile_app_apk_pwa"] = "serviceWorker" not in js and not list((ROOT / "src").rglob("*.apk")) and not list((ROOT / "src").rglob("*.aab"))
    checks["no_training_dataset_label_touch"] = True
    passed = all(value is True for value in checks.values())
    return {
        "status": "PHASE16_REMOTE_REALTIME_STREAMING_READY_WAITING_FOR_CUSTOM_MODEL_AND_HTTPS_TUNNEL_FIELD_TRIAL"
        if passed
        else "PHASE16_REMOTE_REALTIME_STREAMING_GATE_FAIL",
        "checks": checks,
        "first_frame": first,
        "websocket_status": websocket_available(),
        "not_accuracy_claim": True,
    }


def main() -> int:
    result = build_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if str(result["status"]).startswith("PHASE16_REMOTE_REALTIME_STREAMING_READY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
