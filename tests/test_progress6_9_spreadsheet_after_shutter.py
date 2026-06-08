from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_9_spreadsheet_after_shutter_is_local_csv_ready(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    session_id = client.post(
        "/api/field/session/start",
        json={"gps": {"latitude": -7.2234567, "longitude": 112.7312345, "accuracy": 5.0}},
    ).get_json()["session_id"]
    client.post("/api/field/session/shutter", json={"session_id": session_id, "idempotency_key": "P69_SHEET"})
    response = client.get(f"/field-spreadsheet/session/{session_id}")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Spreadsheet Evidence" in html
    assert "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_SPREADSHEET_READY" in html
    assert "Download CSV" in html
    assert "growth_selected_model" in html
    assert f"/field-map/session/{session_id}" in html
