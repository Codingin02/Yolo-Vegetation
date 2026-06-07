from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def run_smoke() -> dict[str, object]:
    client = create_app().test_client()
    capture_response = client.get("/field-capture")
    camera_response = client.get("/field-camera")
    capture = capture_response.get_data(as_text=True)
    camera = camera_response.get_data(as_text=True)
    camera_css = (ROOT / "src" / "ulp_project" / "static" / "field_camera.css").read_text(encoding="utf-8")
    session_js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    checks = {
        "capture_route_200": capture_response.status_code == 200,
        "capture_is_preflight": "capture-preflight-shell" in capture and "start-camera-first" in capture,
        "capture_not_open_long_dashboard": "<h2>Status Ringkas</h2>" not in capture and "<h2>Hasil Kamera / Geometry</h2>" not in capture,
        "developer_debug_default_closed": "<details class=\"glass-card developer-debug\">" in capture and "Developer Debug" in capture,
        "camera_route_200": camera_response.status_code == 200,
        "camera_fullscreen_video": "field-camera-stage" in camera and "video" in camera and "height: 100dvh" in camera_css,
        "facing_mode_environment": 'facingMode: { ideal: "environment" }' in session_js and 'facingMode: "environment"' in session_js,
        "bottom_bar_horizontal": "camera-bottom-bar" in camera and "grid-template-columns" in camera_css,
        "cache_busting": "v=progress6_6" in capture and "v=progress6_6" in camera,
        "ui_version": "progress6_6" in capture and "/api/runtime/ui-version" in "".join(str(rule.rule) for rule in create_app().url_map.iter_rules()),
    }
    return {"status": "PROGRESS_6_6_CAMERA_FIRST_UI_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_6_CAMERA_FIRST_UI_SMOKE_FAIL", "checks": checks}


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
