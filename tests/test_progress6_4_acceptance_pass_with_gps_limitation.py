from __future__ import annotations

from ulp_project.field_acceptance_validation import validate_acceptance_payload


def complete_payload():
    return {
        "submitted_at": "2026-06-07T10:00:00",
        "operator_name": "operator",
        "automatic_checklist": {
            "current_url_mode": "HTTPS_PUBLIC_READY",
            "secure_context": "SECURE_CONTEXT_OK",
            "camera_permission_status": "CAMERA_READY",
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


def test_progress6_4_gps_low_passes_with_limitation_when_other_evidence_complete() -> None:
    payload = complete_payload()
    payload["automatic_checklist"]["gps_status"] = "GPS_ACCURACY_LOW"
    payload["automatic_checklist"]["gps_accuracy_status"] = "GPS_ACCURACY_LOW"
    payload["automatic_checklist"]["gps_accuracy_m"] = 18.0
    payload["automatic_checklist"]["distance_reliability_status"] = "GPS_ACCURACY_GREATER_THAN_DISTANCE"
    result = validate_acceptance_payload(payload)
    assert result["acceptance_status"] == "PHYSICAL_HP_ACCEPTANCE_PASS_WITH_GPS_LIMITATION"
    assert "GPS_LIMITATION_RECORDED_ACCEPTANCE_ALLOWED" in result["reason_codes"]
