from __future__ import annotations

from ulp_project.progress5_4_zone_policy import classify_progress5_4_zone


def test_progress5_4_geometry_zone_policy_thresholds() -> None:
    assert classify_progress5_4_zone(3.0)["zone_status"] == "TEBANG"
    assert classify_progress5_4_zone(3.01)["zone_status"] == "PANTAUAN"
    assert classify_progress5_4_zone(4.0)["zone_status"] == "PANTAUAN"
    assert classify_progress5_4_zone(4.01)["zone_status"] == "AMAN"
    assert classify_progress5_4_zone(None)["zone_status"] == "INSUFFICIENT_DATA"
