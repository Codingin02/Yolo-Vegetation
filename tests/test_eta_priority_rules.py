from __future__ import annotations

from ulp_project.realtime_eta_pipeline import action_for_priority, classify_eta_priority


def test_eta_priority_rules() -> None:
    assert classify_eta_priority(0, 0) == "EMERGENCY"
    assert classify_eta_priority(0.3, 30) == "CRITICAL"
    assert classify_eta_priority(0.9, 90) == "HIGH"
    assert classify_eta_priority(1.8, 180) == "MEDIUM"
    assert classify_eta_priority(3.0, 300) == "LOW"
    assert action_for_priority("EMERGENCY") == "EMERGENCY_CONTACT_OR_NEAR_CONTACT"
