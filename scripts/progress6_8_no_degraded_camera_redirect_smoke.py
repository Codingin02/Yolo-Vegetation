from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project import field_capture_routes  # noqa: E402
from ulp_project.flask_app import create_app  # noqa: E402


def run_smoke() -> dict[str, object]:
    original = field_capture_routes.start_field_session

    def boom(payload, *, runtime_root=None):
        raise RuntimeError("SIMULATED_START_FAILURE")

    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            app = create_app(runtime_root=Path(tmp))
            field_capture_routes.start_field_session = boom
            client = app.test_client()
            response = client.post("/api/field/session/start", json={"point_id": "V001_pohon_sono"})
            payload = response.get_json() or {}
            camera = client.get("/field-camera?session_id=FS_DEGRADED_TEST").get_data(as_text=True)
    finally:
        field_capture_routes.start_field_session = original
    checks = {
        "degraded_start_is_controlled": response.status_code == 202 and payload.get("ok") is False,
        "degraded_has_no_camera_url": payload.get("camera_url") in {None, ""},
        "degraded_has_no_session_id": not str(payload.get("session_id") or ""),
        "field_camera_rejects_fs_degraded": "SESSION_INVALID_OR_EXPIRED" in camera or "FIELD_SESSION_ID_REQUIRED" in camera,
        "no_fs_degraded_camera_redirect": "field-camera?session_id=FS_DEGRADED" not in json.dumps(payload),
    }
    return {
        "status": "PROGRESS_6_8_NO_DEGRADED_CAMERA_REDIRECT_PASS" if all(checks.values()) else "PROGRESS_6_8_NO_DEGRADED_CAMERA_REDIRECT_FAIL",
        "checks": checks,
        "payload": payload,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
