from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_7_double_start_is_idempotent_and_nonempty(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    payload = {"source_mode": "SMOKE_TEST", "idempotency_key": "P67_DOUBLE_START"}
    first = client.post("/api/field/session/start", json=payload).get_json()
    second = client.post("/api/field/session/start", json=payload).get_json()
    assert first["session_id"]
    assert first["session_id"] == second["session_id"]
    assert first["camera_url"] == f"/field-camera?session_id={first['session_id']}"
    assert second["camera_url"] == first["camera_url"]
