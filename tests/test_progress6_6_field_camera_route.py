from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_6_field_camera_route_fullscreen_contract() -> None:
    html = create_app().test_client().get("/field-camera").get_data(as_text=True)
    assert "field-camera-stage" in html
    assert "camera-bottom-bar" in html
    assert "MODEL_NOT_READY_NO_FAKE_DETECTION" in html
    assert "field_camera.js?v=progress6_6" in html
