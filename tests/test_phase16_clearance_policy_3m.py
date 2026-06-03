from ulp_project.safety_clearance_policy import classify_distance_zone, floor_display_meter


def test_display_meter_floor_examples():
    assert floor_display_meter(1.30) == 1
    assert floor_display_meter(2.00) == 2
    assert floor_display_meter(2.75) == 2


def test_three_meter_clearance_policy():
    assert classify_distance_zone(2.9)["distance_zone_status"] == "UNSAFE_WITHIN_3M"
    assert classify_distance_zone(3.0)["distance_zone_status"] == "UNSAFE_WITHIN_3M"
    assert classify_distance_zone(0)["distance_zone_status"] == "CONTACT_OR_OVERLAP"
