from ulp_project.time_to_contact import estimate_time_to_contact


def test_eta_null_if_clearance_or_growth_missing():
    result = estimate_time_to_contact(None, {})
    assert result["status"] == "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA"
    assert result["eta_days"] is None
    result = estimate_time_to_contact(2.0, {})
    assert result["eta_months"] is None


def test_eta_provisional_when_all_growth_inputs_present():
    inputs = {
        "species_base_growth_rate_m_per_day": 0.01,
        "season_multiplier": 1,
        "rainfall_multiplier": 1,
        "humidity_multiplier": 1,
        "temperature_multiplier": 1,
        "soil_ph_multiplier": 1,
        "soil_moisture_multiplier": 1,
        "pruning_history_multiplier": 1,
        "local_calibration_multiplier": 1,
    }
    result = estimate_time_to_contact(3.0, inputs)
    assert result["status"] == "PROVISIONAL_ESTIMATE"
    assert result["eta_days_mid"] == 300.0
