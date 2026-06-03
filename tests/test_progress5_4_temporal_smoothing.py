from __future__ import annotations

from ulp_project.progress5_4_temporal_smoothing import Progress54TemporalSmoother


def test_progress5_4_smoothing_reduces_raw_jitter() -> None:
    smoother = Progress54TemporalSmoother({"smoothing_window": 5, "max_clearance_jump_m_per_update": 0.75, "track_hold_ms": 2000})

    outputs = [smoother.update(value, now_ms=idx * 1000) for idx, value in enumerate([5.0, 5.4, 5.5])]

    assert outputs[-1]["stable_clearance_m"] == 5.4
    assert outputs[-1]["smoothing_status"] == "STABLE_READY"


def test_progress5_4_smoothing_rejects_large_jump_and_holds_tracks() -> None:
    smoother = Progress54TemporalSmoother({"smoothing_window": 5, "max_clearance_jump_m_per_update": 0.75, "track_hold_ms": 2000})
    smoother.update(5.0, now_ms=0)
    jump = smoother.update(6.0, now_ms=1000)
    hold = smoother.update(None, now_ms=2000, object_seen=False)
    lost = smoother.update(None, now_ms=5000, object_seen=False)

    assert jump["smoothing_status"] == "JITTER_REJECTED"
    assert "JITTER_REJECTED" in jump["reason_codes"]
    assert hold["smoothing_status"] == "TRACK_HOLD"
    assert lost["smoothing_status"] == "OBJECT_LOST"
