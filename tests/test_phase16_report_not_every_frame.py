import time

from ulp_project.realtime_streaming import create_realtime_session, process_realtime_frame


def test_realtime_frame_does_not_write_report_by_default(tmp_path):
    session = create_realtime_session(tmp_path)
    payload = {
        "session_id": session["session_id"],
        "session_token": session["session_token"],
        "frame_id": "no_report",
        "timestamp_client_ms": int(time.time() * 1000),
        "point_id": "V001_pohon_sono",
        "species_hint": "pohon_sono",
        "asset_type": "span",
        "client_mode": "remote_https",
        "requested_interval_ms": 1000,
    }
    result = process_realtime_frame(payload)
    assert "report_written" not in result
    assert "report_status" not in result
