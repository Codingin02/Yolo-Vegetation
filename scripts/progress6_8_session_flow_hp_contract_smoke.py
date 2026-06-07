from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def run_smoke() -> dict[str, object]:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        client = create_app(runtime_root=Path(tmp)).test_client()
        home = client.get("/field-capture")
        start = client.post(
            "/api/field/session/start",
            json={
                "point_id": "V001_pohon_sono",
                "idempotency_key": "P68_HP_FLOW",
                "secure_context_status": "SECURE_CONTEXT_OK",
                "current_url_mode": "HTTPS_PUBLIC_READY",
                "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
            },
        )
        start_payload = start.get_json() or {}
        session_id = start_payload.get("session_id")
        camera = client.get(start_payload.get("camera_url") or "/field-camera?session_id=")
        frame = client.post("/api/field/session/frame", json={"session_id": session_id, "frame_image_base64": "bad"})
        gps = client.post(
            "/api/field/session/gps-update",
            json={"session_id": session_id, "coords": {"latitude": -7.2161234, "longitude": 112.7351234, "accuracy": 6.7}, "source": "browser_watchPosition"},
        )
        shutter = client.post("/api/field/session/shutter", json={"session_id": session_id, "idempotency_key": "P68_HP_SHUTTER"})
        shutter_payload = shutter.get_json() or {}
        map_page = client.get(shutter_payload.get("map_url") or f"/field-map/session/{session_id}")
        sheet_page = client.get(shutter_payload.get("spreadsheet_url") or f"/field-spreadsheet/session/{session_id}")
        map_page.get_data()
        sheet_page.get_data()
    checks = {
        "home_200": home.status_code == 200,
        "start_normal_session": start.status_code == 201 and start_payload.get("ok") is True and str(session_id).startswith("FS_") and not str(session_id).startswith("FS_DEGRADED"),
        "camera_url_valid": start_payload.get("camera_url") == f"/field-camera?session_id={session_id}",
        "camera_page_200": camera.status_code == 200,
        "frame_not_404_405_500": frame.status_code not in {404, 405, 500},
        "gps_not_404_405_500": gps.status_code not in {404, 405, 500},
        "shutter_saved": shutter.status_code not in {404, 405, 500} and shutter_payload.get("status") == "FIELD_SESSION_SHUTTER_SAVED",
        "map_after_shutter_200": map_page.status_code == 200,
        "spreadsheet_after_shutter_200": sheet_page.status_code == 200,
    }
    return {
        "status": "PROGRESS_6_8_SESSION_FLOW_HP_CONTRACT_PASS" if all(checks.values()) else "PROGRESS_6_8_SESSION_FLOW_HP_CONTRACT_FAIL",
        "checks": checks,
        "session_id": session_id,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
