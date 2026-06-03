from ulp_project.eta_uncertainty import calculate_eta_to_unsafe_zone


def test_eta_uses_3m_threshold_not_full_clearance():
    result = calculate_eta_to_unsafe_zone(5.0, 0.01)
    assert result["eta_expected_days"] == 200.0


def test_eta_already_within_unsafe_zone():
    result = calculate_eta_to_unsafe_zone(2.5, 0.01)
    assert result["eta_status"] == "ALREADY_WITHIN_UNSAFE_ZONE"
    assert result["eta_expected_days"] == 0
