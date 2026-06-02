from ulp_project.vegetation_clearance import classify_operational_risk, estimate_clearance_from_bboxes


def test_clearance_needs_calibration_without_scale():
    result = estimate_clearance_from_bboxes([0, 0, 10, 10], [20, 0, 30, 10], None, "span")
    assert result["status"] == "CLEARANCE_NOT_READY"
    assert result["calibration_status"] == "CALIBRATION_NOT_READY"


def test_operational_risk_statuses():
    assert classify_operational_risk(None) == "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA"
    assert classify_operational_risk(0.4) == "KRITIS_SEGERA"
    assert classify_operational_risk(4.0) == "PERLU_MONITORING"
