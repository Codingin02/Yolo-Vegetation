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
        payload = {
            "point_id": "V001_pohon_sono",
            "operator_name": "operator_live_hp",
            "secure_context_status": "SECURE_CONTEXT_OK",
            "current_url_mode": "HTTPS_PUBLIC_READY",
            "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
            "camera_status": "CAMERA_READY",
            "gps": {"latitude": -7.2234567, "longitude": 112.7312345, "accuracy": 5.0},
        }
        start = client.post("/api/field/session/start", json=payload)
        start_payload = start.get_json() or {}
        session_id = str(start_payload.get("session_id") or "")
        camera = client.get(f"/field-camera?session_id={session_id}&nocache=progress6_9")
        frame = client.post("/api/field/session/frame", json={"session_id": session_id, "frame_image_base64": "bad"})
        gps = client.post(
            "/api/field/session/gps-update",
            json={"session_id": session_id, "gps": {"current": {"latitude": -7.2234568, "longitude": 112.7312346, "accuracy": 4.8}}},
        )
        camera_html = camera.get_data(as_text=True)
    checks = {
        "start_ok": start.status_code in {201, 202} and start_payload.get("ok") is True,
        "session_id_nonempty": session_id.startswith("FS_") and not session_id.startswith("FS_DEGRADED"),
        "camera_url_has_session": start_payload.get("camera_url") == f"/field-camera?session_id={session_id}",
        "nested_gps_mapped": (start_payload.get("gps") or {}).get("base", {}).get("latitude") == -7.2234567,
        "field_camera_query_read": f'data-session-id="{session_id}"' in camera_html and "FIELD_SESSION_ID_REQUIRED" not in camera_html,
        "frame_no_404_405_500": frame.status_code not in {404, 405, 500},
        "gps_no_404_405_500": gps.status_code not in {404, 405, 500},
        "tree_model_status_split": start_payload.get("tree_model_status") in {"TREE_MODEL_READY_CANDIDATE", "TREE_MODEL_NOT_READY"},
    }
    return {
        "status": "PROGRESS_6_9_SESSION_CAMERA_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_9_SESSION_CAMERA_SMOKE_FAIL",
        "checks": checks,
        "session_id": session_id,
        "tree_model_status": start_payload.get("tree_model_status"),
        "multiclass_model_status": start_payload.get("multiclass_model_status"),
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
