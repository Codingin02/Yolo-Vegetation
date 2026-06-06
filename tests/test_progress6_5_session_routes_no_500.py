from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_5_session_routes_accept_minimal_payload_without_500(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()

    start = client.post("/api/field/session/start", json={"source_mode": "SMOKE_TEST"})
    shutter = client.post("/api/field/session/shutter", json={"source_mode": "SMOKE_TEST"})
    stop = client.post("/api/field/session/stop", json={})

    assert start.status_code != 500
    assert shutter.status_code != 500
    assert stop.status_code != 500
    assert start.get_json()["status"] == "FIELD_SESSION_STARTED"
    assert shutter.get_json()["status"] in {"FIELD_SESSION_SHUTTER_SAVED", "DUPLICATE_SHUTTER_IGNORED"}
    assert stop.get_json()["status"] in {"FIELD_SESSION_STOPPED", "NO_ACTIVE_SESSION_TO_STOP"}
