from ulp_project.safety_clearance_policy import floor_display_meter


def test_floor_does_not_round_up():
    assert floor_display_meter(1.99) == 1
    assert floor_display_meter(0.80) == 0
