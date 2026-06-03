from ulp_project.map_report_policy import should_create_map_marker


def test_map_policy_no_gps_no_marker():
    assert should_create_map_marker({"point_id": "V001"})["write_marker"] is False
    assert should_create_map_marker({"latitude": -7.0, "longitude": 112.0})["write_marker"] is True
