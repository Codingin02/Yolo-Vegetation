from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_6_capture_preflight_not_long_dashboard() -> None:
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)
    assert "capture-preflight-shell" in html
    assert "start-camera-first" in html
    assert "<h2>Status Ringkas</h2>" not in html
    assert "<h2>Hasil Kamera / Geometry</h2>" not in html
    assert "Developer Debug" in html
    assert "<details" in html
