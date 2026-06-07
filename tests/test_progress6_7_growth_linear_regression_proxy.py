from __future__ import annotations

from ulp_project.growth_regression_model import growth_regression_status, predict_growth_regression


def test_progress6_7_growth_regression_proxy_status() -> None:
    status = growth_regression_status()
    assert status["status"] in {
        "GROWTH_LINEAR_REGRESSION_READY_PROXY_DATASET",
        "GROWTH_PRIOR_READY_PROXY_DATASET_NO_REGRESSION",
        "GROWTH_PRIOR_DATASET_NOT_FOUND",
        "GROWTH_PRIOR_DATASET_INVALID",
    }
    assert status["source_status"] == "PROXY_NOT_FIELD_OBSERVED"
    assert status["field_observation_status"] == "NOT_FIELD_MEASURED"
    assert status["not_final_biological_accuracy"] is True


def test_progress6_7_growth_eta_requires_geometry_clearance() -> None:
    result = predict_growth_regression({"point_id": "V001_pohon_sono"})
    assert result["eta_3m_status"] == "INSUFFICIENT_GEOMETRY_DATA"
    assert result["source_status"] == "PROXY_NOT_FIELD_OBSERVED"
