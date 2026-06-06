from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_3_acceptance_does_not_pass_without_hp_evidence(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    latest = client.get("/api/field/acceptance/latest").get_json()
    assert latest["acceptance_status"] == "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"

    partial = client.post("/api/field/acceptance/submit", json={"camera_visible": True}).get_json()
    assert partial["acceptance_status"] in {"PHYSICAL_HP_ACCEPTANCE_PARTIAL", "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"}


def test_progress6_3_acceptance_can_pass_only_with_complete_confirmation(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    payload = {
        "session_id": "ACCEPTANCE_PASS_TEST",
        "current_url_mode": "HTTPS_PUBLIC_READY",
        "secure_context_status": "SECURE_CONTEXT_OK",
        "camera_permission_status": "CAMERA_READY",
        "gps_permission_status": "GPS_READY",
        "gps_accuracy_status": "GPS_ACCURACY_MEDIUM",
        "gps_accuracy_m": 8.0,
        "start_session_status": "PASS",
        "stop_record_status": "PASS",
        "shutter_status": "PASS",
        "report_page_status": "PASS",
        "result_page_status": "PASS",
        "map_status": "MAP_HTML_READY",
        "foreground_recording_status": "FOREGROUND_RECORDING_ACTIVE",
        "no_fake_detection_status": "PASS",
        "operator_name": "operator",
        "hp_different_network_confirmed": True,
        "public_https_url_opened": True,
        "camera_visible": True,
        "gps_active": True,
        "start_record_ok": True,
        "stop_record_ok": True,
        "shutter_recorded": True,
        "report_opened": True,
        "result_opened": True,
        "map_opened_or_no_gps_correct": True,
    }
    passed = client.post("/api/field/acceptance/submit", json=payload).get_json()
    assert passed["acceptance_status"] == "PHYSICAL_HP_ACCEPTANCE_PASS"
