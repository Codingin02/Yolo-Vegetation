from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_7_map_result_spreadsheet_requires_shutter(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    session = client.post("/api/field/session/start", json={"source_mode": "SMOKE_TEST"}).get_json()["session_id"]
    before = client.get(f"/api/field/session/{session}/spreadsheet").get_json()
    assert before["status"] == "RESULT_REQUIRES_SHUTTER"

    shutter = client.post(
        "/api/field/session/shutter",
        json={"session_id": session, "source_mode": "SMOKE_TEST", "idempotency_key": "P67_MAP_RESULT"},
    ).get_json()
    assert shutter["map_enabled"] is True
    assert shutter["result_enabled"] is True
    assert shutter["map_url"] == f"/field-map/session/{session}"
    assert shutter["spreadsheet_url"] == f"/field-spreadsheet/session/{session}"
