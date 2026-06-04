from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress5_4_camera_gps_ui_has_remote_https_diagnostics() -> None:
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)

    for token in [
        "Current URL mode",
        "HTTPS_PUBLIC_READY",
        "LAN_HTTP_DEBUG_ONLY",
        "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED",
        "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED_OPEN_HTTPS_TUNNEL",
        "Copy Public HTTPS URL",
        "Open Public HTTPS URL",
        "camera_permission",
        "gps_permission",
        "model_runtime",
        "frame_interval",
        "last_error",
        "Jangan digunakan sebagai klaim hasil final.",
    ]:
        assert token in html
