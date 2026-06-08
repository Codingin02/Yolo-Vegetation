from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_9_camera_overlay_error_not_visible_for_session_id(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    html = client.get("/field-camera?session_id=FS_VISIBLE_123").get_data(as_text=True)
    assert 'id="camera-session-error" class="camera-session-error-panel" hidden' in html
    assert "FIELD_SESSION_ID_REQUIRED" not in html
    assert "FIELD_SESSION_LOOKUP_PENDING" in html
