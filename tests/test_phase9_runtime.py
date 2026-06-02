from pathlib import Path

import pytest

from ulp_project.flask_app import create_app
from ulp_project.phase9_eta_demo import calculate_manual_eta
from ulp_project.phase9_monitoring import (
    PHASE9_MONITORING_COLUMNS,
    append_monitoring_row,
    build_phase9_monitoring_row,
    write_phase9_risk_map,
)


def test_phase9_manual_eta_calculation():
    result = calculate_manual_eta(0.3, 0.01)
    assert result["status"] == "OK"
    assert result["eta_days"] == 30.0
    assert result["eta_months"] == 0.99
    assert result["risk_priority"] == "CRITICAL"


def test_phase9_missing_clearance_or_growth_is_insufficient():
    assert calculate_manual_eta(None, 0.01)["status"] == "INSUFFICIENT_DATA"
    assert calculate_manual_eta(0.3, None)["status"] == "INSUFFICIENT_DATA"


def test_phase9_upload_endpoint_without_model_does_not_crash(tmp_path, monkeypatch):
    from ulp_project import field_capture

    monkeypatch.setattr(field_capture, "append_monitoring_row", lambda row: {"written": True, "path": str(tmp_path / "report.csv")})
    monkeypatch.setattr(field_capture, "write_phase9_risk_map", lambda row: {"written": False, "path": str(tmp_path / "map.html"), "reason": "NO_GPS_NO_MAP_MARKER"})
    app = create_app(runtime_root=tmp_path)
    client = app.test_client()
    response = client.post(
        "/api/field-capture/upload",
        json={"point_id": "V001_pohon_sono_demo", "species": "pohon_sono", "asset_type": "span", "clearance_m": 0.3, "growth_rate_m_per_day": 0.01},
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["mode"] == "PROVISIONAL_MANUAL_DEMO"
    assert payload["model_status"] == "MODEL_NOT_READY"
    assert payload["eta_days"] == 30.0


def test_phase9_csv_report_row_schema_and_write(tmp_path: Path):
    row = build_phase9_monitoring_row({"point_id": "V001", "status": "OK"})
    assert set(PHASE9_MONITORING_COLUMNS) == set(row)
    result = append_monitoring_row(row, output=tmp_path / "vegetation_risk_monitoring.csv")
    assert result["written"] is True
    assert (tmp_path / "vegetation_risk_monitoring.csv").exists()


def test_phase9_map_marker_requires_gps(tmp_path: Path):
    row = build_phase9_monitoring_row({"point_id": "V001", "status": "OK"})
    no_gps = write_phase9_risk_map(row, output=tmp_path / "map.html")
    assert no_gps["written"] is False
    assert no_gps["reason"] == "NO_GPS_NO_MAP_MARKER"
    row = build_phase9_monitoring_row({"point_id": "V001", "latitude": "-7.0", "longitude": "112.0", "status": "OK"})
    with_gps = write_phase9_risk_map(row, output=tmp_path / "map.html")
    assert with_gps["written"] is True


def test_phase9_no_mobile_app_project_created():
    forbidden_suffixes = {".apk", ".aab"}
    for root in [Path("src"), Path("scripts"), Path("docs"), Path("tests"), Path("configs")]:
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            assert path.suffix.lower() not in forbidden_suffixes
