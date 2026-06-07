from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_7_spreadsheet_result_route_operator_table(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    session = client.post("/api/field/session/start", json={"source_mode": "SMOKE_TEST"}).get_json()["session_id"]
    client.post("/api/field/session/shutter", json={"session_id": session, "source_mode": "SMOKE_TEST", "idempotency_key": "P67_SHEET"})
    api = client.get(f"/api/field/session/{session}/spreadsheet").get_json()
    html = client.get(f"/field-spreadsheet/session/{session}").get_data(as_text=True)
    assert api["status"] == "RESULT_SPREADSHEET_READY"
    assert api["google_sheets_status"] == "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_SPREADSHEET_READY"
    assert "Spreadsheet Evidence" in html
    assert "<table" in html
    assert "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_SPREADSHEET_READY" in html
