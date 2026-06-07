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
        payload = {"point_id": "V001_pohon_sono", "source_mode": "SMOKE_TEST", "idempotency_key": "P67_START_ID"}
        first = client.post("/api/field/session/start", json=payload).get_json() or {}
        second = client.post("/api/field/session/start", json=payload).get_json() or {}
        camera_empty = client.get("/field-camera?session_id=").get_data(as_text=True)
        camera_js = (ROOT / "src" / "ulp_project" / "static" / "field_camera.js").read_text(encoding="utf-8")
        checks = {
            "start_returns_nonempty_session_id": bool(first.get("session_id")),
            "start_returns_camera_url": str(first.get("camera_url", "")).startswith("/field-camera?session_id=FS_"),
            "double_start_idempotent": first.get("session_id") == second.get("session_id"),
            "empty_camera_has_operator_error": "FIELD_SESSION_ID_REQUIRED" in camera_empty,
            "empty_camera_does_not_fallback_to_localstorage": "urlHasSessionParam" in camera_js
            and 'params.get("session_id") || window.localStorage' not in camera_js,
        }
    return {
        "status": "PROGRESS_6_7_SESSION_ID_NAVIGATION_PASS" if all(checks.values()) else "PROGRESS_6_7_SESSION_ID_NAVIGATION_FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
