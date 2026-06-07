from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_6_session_shutter_live_payload_no_500_and_idempotent(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    started = client.post(
        "/api/field/session/start",
        json={
            "point_id": "V001_pohon_sono",
            "base_latitude": -7.2161234,
            "base_longitude": 112.7351234,
            "base_accuracy_m": 3.8,
            "source_mode": "SMOKE_TEST",
        },
    ).get_json()
    payload = {
        "session_id": started["session_id"],
        "idempotency_key": "P66_SHUTTER",
        "current_latitude": -7.2161288,
        "current_longitude": 112.7351288,
        "current_accuracy_m": 6.7,
        "model_status": "MODEL_NOT_READY",
        "source_mode": "SMOKE_TEST",
    }
    first = client.post("/api/field/session/shutter", json=payload)
    second = client.post("/api/field/session/shutter", json=payload)
    assert first.status_code != 500
    assert second.status_code != 500
    assert first.get_json()["status"] == "FIELD_SESSION_SHUTTER_SAVED"
    assert first.get_json()["current_latitude_raw"] == "-7.2161288"
    assert second.get_json()["status"] == "DUPLICATE_SHUTTER_IGNORED"
    assert second.get_json()["csv_appended"] is False
