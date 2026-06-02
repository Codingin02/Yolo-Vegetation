from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app
from ulp_project import phase9_monitoring
from ulp_project.phase9_monitoring import append_monitoring_row, build_phase9_monitoring_row


def test_phase13_csv_lock_falls_back_to_spool(tmp_path, monkeypatch) -> None:
    original = phase9_monitoring._append_row_to_csv
    main_csv = tmp_path / "vegetation_risk_monitoring.csv"
    calls = {"main": 0}

    def locked_main(row, output):
        if output == main_csv:
            calls["main"] += 1
            raise PermissionError("locked by spreadsheet")
        return original(row, output)

    monkeypatch.setattr(phase9_monitoring, "_append_row_to_csv", locked_main)
    monkeypatch.setattr(phase9_monitoring, "SPOOL_DIR", tmp_path / "spool")
    result = append_monitoring_row(build_phase9_monitoring_row({"point_id": "V001"}), output=main_csv, retry_delay_sec=0)
    assert calls["main"] == 3
    assert result["status"] == "REPORT_WRITTEN_SPOOL_CSV_LOCKED"
    assert result["written"] is True
    assert Path(result["path"]).exists()


def test_phase13_api_error_handler_returns_json() -> None:
    app = create_app()

    @app.get("/api/phase13-error")
    def phase13_error():
        raise PermissionError("simulated")

    response = app.test_client().get("/api/phase13-error")
    payload = response.get_json()
    assert response.status_code == 500
    assert payload["status"] == "ERROR"
    assert payload["error_type"] == "PermissionError"
    assert payload["request_path"] == "/api/phase13-error"
    assert "traceback" not in payload


def test_phase13_duplicate_post_is_coalesced(tmp_path) -> None:
    app = create_app(runtime_root=tmp_path)
    client = app.test_client()
    payload = {"point_id": "phase13_dedup_test", "clearance_m": 0.3, "growth_rate_m_per_day": 0.01, "capture_fingerprint": "same-fingerprint"}
    first = client.post("/api/field-capture/upload", json=payload).get_json()
    second = client.post("/api/field-capture/upload", json=payload).get_json()
    assert first["request_dedup_status"] == "ACCEPTED_NEW"
    assert second["request_dedup_status"] == "DUPLICATE_COOLESCED"
    assert second["report_written"] is False


def test_phase13_field_capture_page_has_secure_context_diagnostics() -> None:
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)
    assert "HTTP_LAN" in html
    assert "HTTPS_SECURE" in html
    assert "Kamera/GPS otomatis membutuhkan HTTPS" in html


def test_phase13_frontend_guards_non_json_response() -> None:
    js = Path("src/ulp_project/static/field_capture.js").read_text(encoding="utf-8")
    assert "safeFetchJson" in js
    assert "API_ERROR_NON_JSON_RESPONSE" in js
    assert "content-type" in js
    assert "preview: text.slice(0, 300)" in js
