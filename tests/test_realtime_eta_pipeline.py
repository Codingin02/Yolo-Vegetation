from __future__ import annotations

from ulp_project.realtime_eta_pipeline import run_realtime_eta_pipeline


def test_realtime_eta_pipeline_uses_selected_clearance_and_profile() -> None:
    result = run_realtime_eta_pipeline({"selected_clearance_m": 5.0, "selected_hazard_target": "cable"}, species="pohon_sono")
    assert result["eta_days"] == 200.0
    assert result["eta_months"] == 6.57
    assert result["risk_priority"] == "LOW"
    assert result["action_recommendation"] == "ROUTINE_MONITORING"


def test_realtime_eta_pipeline_unsafe_clearance_eta_zero() -> None:
    result = run_realtime_eta_pipeline({"selected_clearance_m": 2.75, "selected_hazard_target": "cable"}, species="pohon_sono")
    assert result["eta_days"] == 0.0
    assert result["risk_priority"] == "CRITICAL"
    assert result["eta_status"] == "ALREADY_WITHIN_UNSAFE_ZONE"


def test_realtime_eta_pipeline_requires_clearance() -> None:
    result = run_realtime_eta_pipeline({}, species="pohon_sono")
    assert result["eta_days"] is None
    assert result["risk_priority"] == "INSUFFICIENT_DATA"
    assert "selected_clearance_m" in result["required_missing_inputs"]
