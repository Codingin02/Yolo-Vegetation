from __future__ import annotations

from ulp_project.field_session_runtime import gps_accuracy_status


def test_progress6_2_gps_accuracy_thresholds_are_explicit() -> None:
    assert gps_accuracy_status(None)["gps_accuracy_status"] == "GPS_ACCURACY_UNKNOWN"
    assert gps_accuracy_status(5)["gps_accuracy_status"] == "GPS_ACCURACY_GOOD"
    assert gps_accuracy_status(10)["gps_accuracy_status"] == "GPS_ACCURACY_MEDIUM"
    assert gps_accuracy_status(10.1)["gps_accuracy_status"] == "GPS_ACCURACY_LOW"
