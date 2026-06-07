from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_8_frontend_blocks_degraded_session_redirect() -> None:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    camera_js = (ROOT / "src" / "ulp_project" / "static" / "field_camera.js").read_text(encoding="utf-8")
    assert "startsWith(\"FS_DEGRADED\")" in js
    assert "startsWith(\"FS_DEGRADED\")" in camera_js
    assert "SESSION_START_FAILED_NO_CAMERA_REDIRECT" in js


def test_progress6_8_backend_start_exception_has_no_camera_url(monkeypatch, tmp_path) -> None:
    from ulp_project import field_capture_routes
    from ulp_project.flask_app import create_app

    original = field_capture_routes.start_field_session

    def boom(payload, *, runtime_root=None):
        raise RuntimeError("SIMULATED")

    try:
        app = create_app(runtime_root=tmp_path)
        field_capture_routes.start_field_session = boom
        payload = app.test_client().post("/api/field/session/start", json={}).get_json()
    finally:
        field_capture_routes.start_field_session = original
    assert payload["ok"] is False
    assert payload["camera_url"] is None
    assert not payload["session_id"]
