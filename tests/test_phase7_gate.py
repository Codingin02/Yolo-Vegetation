from scripts.phase7_realtime_field_gate import build_phase7_gate_status


def test_phase7_gate_waits_for_labels_model_calibration_env():
    result = build_phase7_gate_status()
    assert result["overall_status"] == "PHASE7_READY_WAITING_FOR_LABELS_MODEL_CALIBRATION_ENVIRONMENT"
    assert result["model_status"] == "MODEL_NOT_READY"
    assert result["field_capture_status"] == "FIELD_CAPTURE_ROUTES_READY"
    assert result["eta_prediction_status"] == "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA"
