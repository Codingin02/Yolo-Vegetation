from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_9_field_camera_empty_session_guard(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    response = client.get("/field-camera")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "FIELD_SESSION_ID_REQUIRED" in html
    assert 'data-session-id=""' in html
    assert "startFrameLoop()" not in html
