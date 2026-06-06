from __future__ import annotations

from ulp_project.field_acceptance_validation import validate_acceptance_payload


def complete_payload(**overrides):
    payload = {
        "acceptance_id": "A6_4_TEST",
        "submitted_at": "2026-06-07T10:00:00",
        "operator_name": "operator",
        "automatic_checklist": {
            "current_url_mode": "HTTPS_PUBLIC_READY",
            "secure_context": "SECURE_CONTEXT_OK",
            "camera_permission_status": "CAMERA_READY",
            "gps_permission_status": "GPS_READY",
            "gps_status": "GPS_READY",
            "gps_accuracy_status": "GPS_ACCURACY_MEDIUM",
            "gps_accuracy_m": 8.0,
            "start_session_status": "PASS",
            "stop_record_status": "PASS",
            "shutter_status": "PASS",
            "report_page_status": "PASS",
            "result_page_status": "PASS",
            "map_status": "MAP_HTML_READY",
            "model_status": "MODEL_NOT_READY",
            "no_fake_detection_status": "PASS",
        },
        "manual_checklist": {"public_https_url_opened": True},
    }
    payload.update(overrides)
    return payload


def test_progress6_4_validator_accepts_complete_model_not_ready_evidence() -> None:
    result = validate_acceptance_payload(complete_payload())
    assert result["acceptance_status"] == "PHYSICAL_HP_ACCEPTANCE_PASS"
    assert result["model_not_ready_allowed"] is True
    assert result["no_fake_acceptance"] is True


def test_progress6_4_validator_fails_without_public_https() -> None:
    payload = complete_payload()
    payload["automatic_checklist"]["current_url_mode"] = "LAN_HTTP_DEBUG_ONLY"
    result = validate_acceptance_payload(payload)
    assert result["acceptance_status"] == "PHYSICAL_HP_ACCEPTANCE_FAIL_NO_PUBLIC_HTTPS"
    assert "public_https_secure_context" in result["missing_requirements"]
