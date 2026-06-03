import time

from ulp_project.realtime_streaming import create_realtime_session, process_realtime_frame


def test_model_missing_does_not_emit_fake_detection(tmp_path):
    session = create_realtime_session(tmp_path)
    result = process_realtime_frame(
        {
            "session_id": session["session_id"],
            "session_token": session["session_token"],
            "frame_id": "model_missing",
            "timestamp_client_ms": int(time.time() * 1000),
            "point_id": "V001_pohon_sono",
            "species_hint": "pohon_sono",
            "asset_type": "span",
            "client_mode": "remote_https",
            "requested_interval_ms": 1000,
        }
    )
    assert result["model_status"] == "MODEL_NOT_READY"
    assert result["detections"] == []
    assert result["no_fake_detection"] is True
