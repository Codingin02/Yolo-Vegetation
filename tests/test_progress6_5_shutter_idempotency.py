from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_5_duplicate_shutter_key_is_ignored(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    start = client.post(
        "/api/field/session/start",
        json={
            "session_id": "P65_IDEMPOTENCY_TEST",
            "source_mode": "SMOKE_TEST",
            "base_gps": {"latitude": -7.1234567, "longitude": 112.7654321, "accuracy": 8},
        },
    ).get_json()
    payload = {"session_id": start["session_id"], "source_mode": "SMOKE_TEST", "idempotency_key": "P65_DUPLICATE_KEY"}

    first = client.post("/api/field/session/shutter", json=payload).get_json()
    second = client.post("/api/field/session/shutter", json=payload).get_json()

    assert first["status"] == "FIELD_SESSION_SHUTTER_SAVED"
    assert first["csv_appended"] is True
    assert second["status"] == "DUPLICATE_SHUTTER_IGNORED"
    assert second["csv_appended"] is False
    assert second["duplicate_ignored"] is True
