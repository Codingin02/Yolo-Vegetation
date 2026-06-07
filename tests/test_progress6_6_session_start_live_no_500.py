from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_6_session_start_live_payload_no_500(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    response = client.post(
        "/api/field/session/start",
        json={
            "point_id": "V001_pohon_sono",
            "operator_name": "",
            "notes": "",
            "secure_context_status": "SECURE_CONTEXT_OK",
            "current_url_mode": "HTTPS_PUBLIC_READY",
            "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
            "camera_status": "CAMERA_READY",
            "gps_status": "GPS_READY",
            "gps_source": "GPS_SOURCE_BROWSER",
            "base_latitude": -7.2161234,
            "base_longitude": 112.7351234,
            "base_accuracy_m": 3.8,
            "source_mode": "SMOKE_TEST",
        },
    )
    payload = response.get_json()
    assert response.status_code != 500
    assert payload["status"] == "FIELD_SESSION_STARTED"
    assert payload["gps"]["base"]["latitude_raw"] == "-7.2161234"
    assert payload["model_status"] == "MODEL_NOT_READY"
    assert payload["no_fake_detection"] is True
