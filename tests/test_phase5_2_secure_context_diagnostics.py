from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_phase5_2_secure_context_diagnostic_tokens_present() -> None:
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)
    assert "LOCAL_DEV_CONTEXT" in html
    assert "INSECURE_CONTEXT_CAMERA_GPS_MAY_FAIL" in html
    assert "SECURE_CONTEXT_EXPECTED" in html
    assert "HTTPS_SECURE" in html
    assert "HTTP_LAN" in html


def test_phase5_2_camera_gps_error_codes_present_in_frontend() -> None:
    js = Path("src/ulp_project/static/field_capture.js").read_text(encoding="utf-8")
    assert "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT" in js
    assert "GPS_PERMISSION_DENIED" in js
    assert "GPS_TIMEOUT" in js
    assert "GPS_SOURCE_MANUAL" in js
