from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_9_field_camera_query_session_id_reaches_template(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    response = client.get("/field-camera?session_id=FS_TEST_123&nocache=progress6_9")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'data-session-id="FS_TEST_123"' in html
    assert "FS_TEST_123" in html
    assert "FIELD_SESSION_ID_REQUIRED" not in html
