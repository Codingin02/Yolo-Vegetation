from __future__ import annotations

from ulp_project.gps_reliability_policy import distance_reliability
from ulp_project.gps_truth_policy import validate_gps_evidence


def test_progress6_5_gps_accuracy_above_25m_does_not_create_marker() -> None:
    result = validate_gps_evidence({"latitude": -7.1234567, "longitude": 112.7654321, "accuracy": 26})
    assert result["status"] == "NO_GPS_NO_MARKER"
    assert "GPS_ACCURACY_TOO_LOW_FOR_MARKER" in result["gps_quality_reasons"]


def test_progress6_5_accuracy_greater_than_distance_has_new_reliability_alias() -> None:
    base = {"latitude": -7.1234567, "longitude": 112.7654321, "accuracy": 8}
    current = {"latitude": -7.1234570, "longitude": 112.7654321, "accuracy": 8}
    result = distance_reliability(base, current)
    assert result["distance_reliability_status"] == "GPS_ACCURACY_GREATER_THAN_DISTANCE"
    assert result["distance_reliability_status_progress6_5"] == "DISTANCE_NOT_RELIABLE_ACCURACY_GT_DISTANCE"
    assert result["is_distance_reliable"] is False
