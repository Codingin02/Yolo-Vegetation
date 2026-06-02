from ulp_project.calibration import estimate_pixel_scale
from ulp_project.distance_estimation import classify_clearance_risk, estimate_object_distance_to_conductor


def test_no_calibration_returns_not_ready():
    result = estimate_object_distance_to_conductor((0, 0), (10, 0), meters_per_pixel=None, calibration_config={})
    assert result["status"] == "CALIBRATION_NOT_READY"


def test_distance_and_clearance_classification():
    scale = estimate_pixel_scale(known_object_width_m=2.0, known_object_width_px=100)
    assert scale["meters_per_pixel"] == 0.02
    distance = estimate_object_distance_to_conductor((0, 0), (100, 0), meters_per_pixel=0.02)
    assert distance["status"] == "READY"
    assert distance["distance_m"] == 2.0
    assert classify_clearance_risk(1.0)["risk_level"] == "danger"
    assert classify_clearance_risk(2.0)["risk_level"] == "warning"
    assert classify_clearance_risk(3.0)["risk_level"] == "safe"
