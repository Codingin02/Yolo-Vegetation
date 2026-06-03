from ulp_project.eta_explanation import explain_eta
from ulp_project.eta_uncertainty import calculate_eta_to_unsafe_zone


def test_eta_explanation_not_accuracy_claim():
    eta = calculate_eta_to_unsafe_zone(5.0, 0.01)
    explanation = explain_eta(eta, {"calibration_status": "CALIBRATION_NOT_READY"})
    assert explanation["confidence_status"] == "PROVISIONAL_CALIBRATION_NOT_READY"
    assert explanation["not_accuracy_claim"] is True
