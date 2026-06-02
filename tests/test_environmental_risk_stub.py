from ulp_project.environmental_risk import score_environmental_risk


def test_environmental_risk_waits_for_real_data():
    result = score_environmental_risk({})
    assert result["status"] == "DATA_NOT_READY"
    assert result["risk_score"] is None
    assert result["risk_level"] == "UNKNOWN"


def test_environmental_risk_full_input_is_still_stub():
    result = score_environmental_risk(
        {
            "soil_ph": 7,
            "rainfall_mm": 100,
            "humidity_percent": 70,
            "temperature_c": 30,
            "season_label": "pending_validation",
            "tree_species": "pohon_sono",
            "distance_to_conductor_m": 1.5,
            "growth_stage": "unknown",
            "maintenance_history": "unknown",
        }
    )
    assert result["status"] == "RULE_BASED_STUB"
    assert result["risk_score"] is None
