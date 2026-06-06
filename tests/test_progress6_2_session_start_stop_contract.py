from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_2_session_start_stop_contract(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()

    start = client.post(
        "/api/field/session/start",
        json={
            "session_id": "TEST_SESSION_START_STOP",
            "point_id": "V001_pohon_sono",
            "operator_name": "operator-test",
            "secure_context_status": "SECURE_CONTEXT_OK",
            "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
            "camera_status": "CAMERA_READY",
            "base_gps": {"latitude": -7.1, "longitude": 112.7, "accuracy": 8, "source": "GPS_SOURCE_BROWSER"},
        },
    ).get_json()
    assert start["status"] == "FIELD_SESSION_STARTED"
    assert start["session_status"] == "RECORDING_ACTIVE"
    assert start["no_fake_gps"] is True
    assert start["no_fake_detection"] is True

    stopped = client.post("/api/field/session/stop", json={"session_id": start["session_id"]}).get_json()
    assert stopped["status"] == "FIELD_SESSION_STOPPED"
    assert stopped["session_status"] == "RECORDING_STOPPED"
