from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress5_4_realtime_frame_model_not_ready_no_autosave() -> None:
    payload = create_app().test_client().post(
        "/api/field/realtime-frame",
        json={"point_id": "V001_pohon_sono", "timestamp_client_ms": 0, "current_url_mode": "HTTPS_PUBLIC_READY"},
    ).get_json()

    assert payload["model_status"] == "MODEL_NOT_READY"
    assert payload["detections"] == []
    assert payload["inference_source"] == "SKIPPED_NO_MODEL"
    assert payload["no_autosave_on_realtime_frame"] is True
    assert payload["overlay_json"]["message"] == "MODEL_NOT_READY_NO_FAKE_DETECTION"
