from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_7_field_camera_empty_session_shows_operator_error() -> None:
    html = create_app().test_client().get("/field-camera?session_id=").get_data(as_text=True)
    assert "FIELD_SESSION_ID_REQUIRED" in html
    assert "Back to Home" in html


def test_progress6_7_frame_missing_session_does_not_use_latest(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    client.post("/api/field/session/start", json={"source_mode": "SMOKE_TEST"})
    response = client.post("/api/field/session/frame", json={"frame_image_base64": ""})
    assert response.status_code == 400
    assert response.get_json()["status"] == "FIELD_SESSION_ID_REQUIRED"
