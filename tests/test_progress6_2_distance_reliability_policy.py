from __future__ import annotations

from ulp_project.field_session_runtime import distance_reliability


def test_progress6_2_distance_reliability_rejects_accuracy_larger_than_distance() -> None:
    base = {"latitude": -7.0, "longitude": 112.0, "accuracy": 12}
    current = {"latitude": -7.00001, "longitude": 112.0, "accuracy": 12}

    result = distance_reliability(base, current)

    assert result["is_distance_reliable"] is False
    assert result["distance_reliability_status"] == "GPS_ACCURACY_GREATER_THAN_DISTANCE"


def test_progress6_2_distance_reliability_accepts_distance_larger_than_accuracy() -> None:
    base = {"latitude": -7.0, "longitude": 112.0, "accuracy": 3}
    current = {"latitude": -7.001, "longitude": 112.0, "accuracy": 3}

    result = distance_reliability(base, current)

    assert result["is_distance_reliable"] is True
    assert result["distance_reliability_status"] == "DISTANCE_RELIABLE_WITH_BROWSER_GPS_LIMITS"
