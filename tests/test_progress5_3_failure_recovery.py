from __future__ import annotations

from ulp_project.operator_failure_recovery import build_failure_recovery


def test_failure_recovery_catches_localhost_used_on_hp() -> None:
    result = build_failure_recovery({"url_attempted": "http://localhost:5000/field-capture", "hp_can_open_url": False})

    assert result["status"] == "FAILURE_RECOVERY_DECISION_READY"
    assert result["severity"] == "HIGH"
    assert "localhost" in result["likely_cause"].lower()
    assert result["exact_command"] == "ngrok http 5000"


def test_failure_recovery_camera_and_gps_statuses() -> None:
    camera = build_failure_recovery({"hp_can_open_url": True, "camera_status": "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT"})
    gps = build_failure_recovery({"hp_can_open_url": True, "gps_status": "GPS_PERMISSION_DENIED"})

    assert camera["severity"] == "MEDIUM"
    assert "HTTPS ngrok" in camera["next_action"]
    assert gps["severity"] == "MEDIUM"
    assert "Location permission" in gps["next_action"]


def test_failure_recovery_preserves_model_not_ready_safe_mode() -> None:
    result = build_failure_recovery({"hp_can_open_url": True, "model_status": "MODEL_NOT_READY", "calibration_status": "CALIBRATION_READY"})

    assert result["severity"] == "INFO"
    assert "jangan klaim real model" in result["next_action"]
    assert "detections tetap []" in result["operator_note"]
