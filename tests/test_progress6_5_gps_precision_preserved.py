from __future__ import annotations

from ulp_project.gps_truth_policy import format_coordinate_raw, validate_gps_evidence


def test_progress6_5_gps_raw_coordinates_keep_seven_decimals() -> None:
    assert format_coordinate_raw(-7.123456789) == "-7.1234568"
    assert format_coordinate_raw(112.76543219) == "112.7654322"


def test_progress6_5_rounded_coordinates_are_not_marker_ready() -> None:
    result = validate_gps_evidence({"latitude": -7.1, "longitude": 112.7, "accuracy": 8})
    assert result["status"] == "NO_GPS_NO_MARKER"
    assert result["gps_precision_status"] == "GPS_PRECISION_LOST_ROUNDED_COORDINATE"
