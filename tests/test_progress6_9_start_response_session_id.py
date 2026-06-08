from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_9_start_response_has_normal_session_and_camera_url(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    payload = {
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
    }
    response = client.post("/api/field/session/start", json=payload)
    data = response.get_json()
    assert response.status_code in {201, 202}
    assert data["ok"] is True
    assert data["degraded"] is False
    assert data["session_id"].startswith("FS_")
    assert not data["session_id"].startswith("FS_DEGRADED")
    assert data["camera_url"] == f"/field-camera?session_id={data['session_id']}"
