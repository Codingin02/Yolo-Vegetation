from __future__ import annotations

from ulp_project.gps_reliability_policy import distance_reliability, gps_accuracy_status


def test_progress6_3_gps_accuracy_hardened_thresholds() -> None:
    assert gps_accuracy_status(None)["gps_accuracy_status"] == "GPS_ACCURACY_UNKNOWN"
    assert gps_accuracy_status(5)["gps_accuracy_status"] == "GPS_ACCURACY_GOOD"
    assert gps_accuracy_status(10)["gps_accuracy_status"] == "GPS_ACCURACY_MEDIUM"
    assert gps_accuracy_status(10.1)["gps_accuracy_status"] == "GPS_ACCURACY_LOW"
    assert "klaim jarak presisi" in gps_accuracy_status(12)["operator_message"]


def test_progress6_3_distance_reliability_rejects_accuracy_larger_than_distance() -> None:
    base = {"latitude": -7.0, "longitude": 110.0, "accuracy": 8}
    current = {"latitude": -7.0, "longitude": 110.00001, "accuracy": 8}
    result = distance_reliability(base, current)
    assert result["is_distance_reliable"] is False
    assert result["distance_reliability_status"] == "GPS_ACCURACY_GREATER_THAN_DISTANCE"


def test_progress6_3_distance_reliability_accepts_field_evidence_distance() -> None:
    base = {"latitude": -7.0, "longitude": 110.0, "accuracy": 5}
    current = {"latitude": -7.0, "longitude": 110.001, "accuracy": 5}
    result = distance_reliability(base, current)
    assert result["is_distance_reliable"] is True
    assert result["distance_reliability_status"] == "DISTANCE_REASONABLY_RELIABLE_FOR_FIELD_EVIDENCE"
