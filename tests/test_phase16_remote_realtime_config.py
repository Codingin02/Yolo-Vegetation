from ulp_project.safety_clearance_policy import load_safety_clearance_policy


def test_phase16_policy_config_loaded():
    policy = load_safety_clearance_policy()
    assert policy["safe_clearance_min_m"] == 3.0
    assert policy["distance_zone_actions"]["UNSAFE_WITHIN_3M"] == "PRIORITY_PRUNING_REVIEW"
