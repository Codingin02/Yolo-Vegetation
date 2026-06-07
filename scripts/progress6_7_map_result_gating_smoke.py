from __future__ import annotations

import base64
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402

PNG_1X1 = "data:image/png;base64," + base64.b64encode(
    base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")
).decode("ascii")


def run_smoke() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        client = create_app(runtime_root=Path(tmp)).test_client()
        start = client.post("/api/field/session/start", json={"source_mode": "SMOKE_TEST", "idempotency_key": "P67_GATE"}).get_json() or {}
        session_id = start.get("session_id")
        before = client.get(f"/api/field/session/{session_id}/spreadsheet").get_json() or {}
        shutter = client.post(
            "/api/field/session/shutter",
            json={
                "session_id": session_id,
                "source_mode": "SMOKE_TEST",
                "idempotency_key": "P67_GATE_SHUTTER",
                "frame_image_base64": PNG_1X1,
                "current_latitude": -7.2161234,
                "current_longitude": 112.7351234,
                "current_accuracy_m": 6.7,
            },
        ).get_json() or {}
        after = client.get(f"/api/field/session/{session_id}/spreadsheet").get_json() or {}
        camera = client.get(f"/field-camera?session_id={session_id}").get_data(as_text=True)
        checks = {
            "before_shutter_result_requires_shutter": before.get("status") == "RESULT_REQUIRES_SHUTTER",
            "shutter_has_map_url": shutter.get("map_url") == f"/field-map/session/{session_id}",
            "shutter_has_spreadsheet_url": shutter.get("spreadsheet_url") == f"/field-spreadsheet/session/{session_id}",
            "after_shutter_spreadsheet_ready": after.get("status") == "RESULT_SPREADSHEET_READY",
            "camera_map_result_disabled_initially": 'id="open-map-report"' in camera and "disabled" in camera and 'id="session-result"' in camera,
            "camera_uses_session_map_not_api_latest": "/field-map/session/" in camera and "/api/field/latest-map" not in camera,
            "camera_result_uses_spreadsheet": "/field-spreadsheet/session/" in (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8"),
        }
    return {
        "status": "PROGRESS_6_7_MAP_RESULT_GATING_PASS" if all(checks.values()) else "PROGRESS_6_7_MAP_RESULT_GATING_FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
