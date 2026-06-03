from ulp_project.measurement_quality import build_measurement_quality_report


def test_measurement_quality_reason_codes():
    result = build_measurement_quality_report({"model_status": "MODEL_NOT_READY", "calibration_status": "CALIBRATION_NOT_READY", "gps_ready": False})
    assert result["status"] == "MEASUREMENT_QUALITY_READY"
    assert "MODEL_NOT_READY" in result["reason_codes"]
    assert result["measurement_quality_label"] in {"VERY_LOW", "LOW", "MEDIUM", "HIGH", "FIELD_CONFIRMED"}
