from __future__ import annotations

import time

from ulp_project.phase5_2_field_trial import write_field_trial_snapshot_report
from ulp_project.realtime_streaming import create_realtime_session, process_realtime_frame


def test_phase5_2_realtime_frame_does_not_write_report(tmp_path) -> None:
    session = create_realtime_session(tmp_path)
    result = process_realtime_frame(
        {
            "session_id": session["session_id"],
            "session_token": session["session_token"],
            "frame_id": "report_snapshot_only",
            "timestamp_client_ms": int(time.time() * 1000),
            "point_id": "V001_pohon_sono",
            "species_hint": "pohon_sono",
            "asset_type": "span",
            "client_mode": "remote_https",
            "requested_interval_ms": 1000,
        }
    )
    assert "report_written" not in result
    assert "report_status" not in result


def test_phase5_2_snapshot_submit_writes_report(tmp_path) -> None:
    result = write_field_trial_snapshot_report(
        {"point_id": "V001_pohon_sono", "clearance_m": 5.0, "growth_rate_m_per_day": 0.01},
        output=tmp_path / "snapshot.csv",
        map_output=tmp_path / "map.html",
    )
    assert result["report_written"] is True
    assert (tmp_path / "snapshot.csv").exists()
