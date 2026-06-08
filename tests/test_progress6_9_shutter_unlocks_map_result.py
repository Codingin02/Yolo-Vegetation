from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_9_shutter_unlocks_map_and_result(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    session_id = client.post(
        "/api/field/session/start",
        json={"gps": {"latitude": -7.2234567, "longitude": 112.7312345, "accuracy": 5.0}},
    ).get_json()["session_id"]

    before = client.get(f"/field-map/session/{session_id}").get_data(as_text=True)
    assert "MAP_LOCKED_SHUTTER_REQUIRED" in before

    shutter = client.post("/api/field/session/shutter", json={"session_id": session_id, "idempotency_key": "P69_SHUTTER"}).get_json()
    assert shutter["status"] == "FIELD_SESSION_SHUTTER_SAVED"
    assert shutter["map_enabled"] is True
    assert shutter["result_enabled"] is True
    assert shutter["map_url"] == f"/field-map/session/{session_id}"
    assert shutter["spreadsheet_url"] == f"/field-spreadsheet/session/{session_id}"
