from __future__ import annotations

from ulp_project.calibration_readiness import check_calibration_readiness
from ulp_project.environmental_readiness import check_environmental_readiness
from ulp_project.google_sheets_export import export_google_sheets_ready_csv
from ulp_project.realtime_field_pipeline import pipeline_status, process_realtime_inspection
from ulp_project.yolo_inference_adapter import run_yolo_or_manual_fallback


def test_phase12_pipeline_demo_generates_eta_without_label_or_model(tmp_path) -> None:
    result = process_realtime_inspection(
        {"point_id": "V001_pohon_sono", "clearance_m": 0.3, "growth_rate_m_per_day": 0.01},
        write_outputs=True,
        report_output=tmp_path / "report.csv",
        map_output=tmp_path / "map.html",
    )
    assert result["eta_days"] == 30.0
    assert result["report_written"] is True
    assert result["map_marker_written"] is False
    assert result["model_status"] == "MODEL_NOT_READY"


def test_phase12_google_sheets_not_configured_does_not_crash() -> None:
    result = export_google_sheets_ready_csv(mode="dry-run")
    assert result["credential_status"] == "GOOGLE_SHEETS_NOT_CONFIGURED"
    assert result["live_push"] is False


def test_phase12_calibration_missing_does_not_create_fake_values() -> None:
    result = check_calibration_readiness({})
    assert result["status"] == "CALIBRATION_WAITING_FOR_FIELD_DATA"
    assert "pixel_to_meter_ratio" in result["missing_inputs"]


def test_phase12_environment_missing_is_manual_required_or_partial() -> None:
    result = check_environmental_readiness(values={})
    assert result["status"] in {"ENVIRONMENT_PARTIAL", "ENVIRONMENT_MANUAL_REQUIRED"}
    assert result["not_fake_environment"] is True


def test_phase12_yolo_fallback_keeps_manual_path() -> None:
    result = run_yolo_or_manual_fallback(input_path="manual-demo.jpg")
    assert result["status"] == "MODEL_NOT_READY"
    assert result["detections"] == []
    assert result["fallback"] == "MANUAL_PROVISIONAL_INPUT"


def test_phase12_status_is_safe_waiting_for_labels() -> None:
    result = pipeline_status()
    assert result["dataset_status"] == "WAITING_FOR_LABELS"
    assert result["training_status"].startswith("BLOCKED")
