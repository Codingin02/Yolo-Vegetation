from ulp_project.risk_stub import evaluate_vegetation_risk


def test_risk_stub_does_not_claim_final_score_without_env_data():
    result = evaluate_vegetation_risk({})
    assert result.status == "ENV_DATA_NOT_AVAILABLE"
    assert result.risk_score is None
    assert result.risk_level == "UNKNOWN"
    assert result.missing_inputs
