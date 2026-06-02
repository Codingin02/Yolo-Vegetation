from ulp_project.vegetation_risk_model import score_pohon_sono_risk


def test_risk_model_does_not_invent_scores_when_sources_empty():
    result = score_pohon_sono_risk({})
    assert result["status"] == "ENVIRONMENTAL_DATA_NOT_READY"
    assert result["confidence_level"] == "LOW"
    assert result["growth_pressure_score"] is None
    assert result["not_accuracy_claim"] is True


def test_risk_model_low_confidence_with_partial_manual_data():
    result = score_pohon_sono_risk(
        {
            "point_id": "V001_pohon_sono",
            "rainfall_7d_mm": 40,
            "relative_humidity_2m_percent": 80,
        }
    )
    assert result["status"] == "RULE_BASED_STUB"
    assert result["confidence_level"] == "LOW"
    assert 0 <= result["growth_pressure_score"] <= 100
    assert "VISION_CLEARANCE_NOT_READY" in result["data_quality_flags"]
