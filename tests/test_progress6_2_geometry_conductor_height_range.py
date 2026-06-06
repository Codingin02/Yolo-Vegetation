from __future__ import annotations

from ulp_project.field_session_runtime import classify_clearance, validate_conductor_height


def test_progress6_2_conductor_height_range_is_guarded() -> None:
    assert validate_conductor_height(0.5)["status"] == "CONDUCTOR_HEIGHT_OUT_OF_CONFIG_RANGE"
    assert validate_conductor_height(12.5)["status"] == "CONDUCTOR_HEIGHT_OUT_OF_CONFIG_RANGE"
    assert validate_conductor_height(11.0)["status"] == "CONDUCTOR_HEIGHT_IN_CONFIG_RANGE"


def test_progress6_2_clearance_zone_policy_uses_safe_config_default() -> None:
    assert classify_clearance(tree_height_m=8.2, conductor_height_m=11.0)["zone_status"] == "TEBANG"
    assert classify_clearance(tree_height_m=7.5, conductor_height_m=11.0)["zone_status"] == "PANTAUAN"
    assert classify_clearance(tree_height_m=6.5, conductor_height_m=11.0)["zone_status"] == "AMAN"
    assert classify_clearance(tree_height_m=None, conductor_height_m=11.0)["zone_status"] == "INSUFFICIENT_DATA"
