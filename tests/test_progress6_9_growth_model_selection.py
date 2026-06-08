from __future__ import annotations

from ulp_project.growth_regression_model import growth_regression_status, predict_growth_regression


def test_progress6_9_growth_model_selection_has_metrics_or_safe_fallback() -> None:
    status = growth_regression_status()
    assert status["source_status"] == "PROXY_NOT_FIELD_OBSERVED"
    assert status["not_final_biological_accuracy"] is True
    assert status["growth_model_status"] in {
        "GROWTH_MODEL_READY_PROXY_VALIDATED",
        "GROWTH_MODEL_PROXY_FALLBACK_READY",
        "GROWTH_MODEL_NOT_READY_NO_DATA",
    }
    if status["growth_model_status"] == "GROWTH_MODEL_READY_PROXY_VALIDATED":
        assert status["selected_model_name"]
        assert status["validation_mae"] is not None
        assert status["validation_rmse"] is not None
        assert "feature_columns" in status
        assert status["target_column"]


def test_progress6_9_growth_prediction_eta_requires_geometry() -> None:
    prediction = predict_growth_regression({})
    assert prediction["source_status"] == "PROXY_NOT_FIELD_OBSERVED"
    assert prediction["eta_3m_status"] == "INSUFFICIENT_GEOMETRY_DATA"
    assert prediction["not_final_biological_accuracy"] is True
