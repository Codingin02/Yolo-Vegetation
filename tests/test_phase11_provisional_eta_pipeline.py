from __future__ import annotations

from ulp_project.field_inspection_record import FieldInspectionRecord
from ulp_project.phase9_monitoring import PHASE9_MONITORING_COLUMNS, build_phase9_monitoring_row, write_phase9_risk_map
from ulp_project.realtime_eta_engine import estimate_realtime_eta


def test_phase11_eta_is_calculated_from_manual_clearance_and_growth() -> None:
    record = FieldInspectionRecord.from_payload({"clearance_m": 0.3, "growth_rate_m_per_day": 0.01})
    result = estimate_realtime_eta(record)
    assert result.eta_days == 30.0
    assert result.eta_months == 0.99
    assert result.risk_priority == "CRITICAL"
    assert result.environmental_data_status == "ENVIRONMENT_PARTIAL"


def test_phase11_eta_null_when_input_incomplete() -> None:
    record = FieldInspectionRecord.from_payload({"clearance_m": 0.3})
    result = estimate_realtime_eta(record)
    assert result.status == "INSUFFICIENT_DATA"
    assert result.eta_days is None
    assert "growth_rate_m_per_day" in result.required_missing_inputs


def test_phase11_monitoring_schema_contains_required_columns() -> None:
    required = {
        "inspection_id",
        "timestamp",
        "point_id",
        "species",
        "asset_type",
        "clearance_m",
        "growth_rate_m_per_day",
        "adjusted_growth_rate_m_per_day",
        "eta_days",
        "eta_months",
        "risk_priority",
        "action_recommendation",
        "environmental_source",
        "measurement_source",
        "confidence_status",
        "photo_path",
        "map_link",
    }
    assert required.issubset(set(PHASE9_MONITORING_COLUMNS))
    row = build_phase9_monitoring_row({"point_id": "V001_pohon_sono"})
    assert set(row).issubset(set(PHASE9_MONITORING_COLUMNS))


def test_phase11_map_does_not_create_marker_without_gps(tmp_path) -> None:
    output = tmp_path / "map.html"
    result = write_phase9_risk_map(build_phase9_monitoring_row({"point_id": "V001_pohon_sono"}), output=output)
    assert result["written"] is False
    assert result["reason"] == "NO_GPS_NO_MAP_MARKER"
    assert not output.exists()
