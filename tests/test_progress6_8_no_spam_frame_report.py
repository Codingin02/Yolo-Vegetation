from __future__ import annotations

from ulp_project.realtime_stability_filter import apply_stability_filter, reset_stability_filter


def test_progress6_8_realtime_frames_do_not_write_report_per_frame() -> None:
    session_id = "P68_NO_SPAM"
    reset_stability_filter(session_id)
    for index in range(6):
        result = apply_stability_filter(session_id, {"tree_detected": index % 2 == 0}, now=200.0 + index)
        assert result["no_spam_report_per_frame"] is True
