from __future__ import annotations

from ulp_project.growth_prediction_runtime import predict_growth_prior


def test_progress6_6_growth_prior_predictor_returns_eta_only_with_clearance() -> None:
    with_clearance = predict_growth_prior({"point_id": "V001_pohon_sono", "clearance_m": 4.5, "soil_ph_actual": 6.5})
    without_clearance = predict_growth_prior({"point_id": "V001_pohon_sono"})
    assert with_clearance["source_status"] == "PROXY_NOT_FIELD_OBSERVED"
    assert with_clearance["estimated_height_growth_m_per_year"] > 0
    assert with_clearance["eta_to_3m_clearance_days"] != "INSUFFICIENT_GEOMETRY_DATA"
    assert without_clearance["eta_to_3m_clearance_days"] == "INSUFFICIENT_GEOMETRY_DATA"
