import time

from ulp_project.realtime_streaming import create_realtime_session, process_realtime_frame


def _payload(session, frame_id):
    return {
        "session_id": session["session_id"],
        "session_token": session["session_token"],
        "frame_id": frame_id,
        "timestamp_client_ms": int(time.time() * 1000),
        "point_id": "V001_pohon_sono",
        "species_hint": "pohon_sono",
        "asset_type": "span",
        "client_mode": "remote_https",
        "requested_interval_ms": 1000,
    }


def test_frame_rate_limit_one_fps(tmp_path):
    session = create_realtime_session(tmp_path)
    first = process_realtime_frame(_payload(session, "f1"))
    second = process_realtime_frame(_payload(session, "f2"))
    assert first["status"] == "REALTIME_FRAME_PROCESSED"
    assert second["status"] == "FRAME_RATE_LIMITED"
