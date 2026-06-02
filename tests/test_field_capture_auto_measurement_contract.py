from __future__ import annotations

from ulp_project.flask_app import create_app
from ulp_project.phase9_monitoring import PHASE9_MONITORING_COLUMNS


def test_field_capture_reports_auto_measurement_model_not_ready(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    response = client.post(
        "/api/field-capture/upload",
        json={"point_id": "V001_pohon_sono_auto", "capture_fingerprint": "phase14-contract"},
    )
    payload = response.get_json()
    assert response.status_code == 202
    assert payload["auto_measurement_status"] == "AUTO_MEASUREMENT_NOT_READY"
    assert payload["auto_model_status"] == "MODEL_NOT_READY"
    assert payload["not_accuracy_claim"] is True


def test_csv_schema_has_auto_measurement_columns() -> None:
    required = {
        "auto_measurement_status",
        "auto_model_status",
        "detected_objects",
        "auto_tree_height_m",
        "auto_pole_height_m",
        "auto_cable_height_m",
        "auto_span_lowest_point_height_m",
        "clearance_to_cable_m",
        "clearance_to_span_m",
        "selected_clearance_m",
        "selected_hazard_target",
        "measurement_confidence",
        "raw_selected_clearance_m",
        "stabilized_selected_clearance_m",
        "stabilization_status",
    }
    assert required.issubset(set(PHASE9_MONITORING_COLUMNS))
