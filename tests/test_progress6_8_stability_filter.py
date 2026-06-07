from __future__ import annotations

from ulp_project.realtime_stability_filter import apply_stability_filter, reset_stability_filter


def test_progress6_8_stability_filter_holds_until_window_ready() -> None:
    session_id = "P68_TEST_STABILITY"
    reset_stability_filter(session_id)
    first = apply_stability_filter(session_id, {"tree_detected": True, "detected_classes": ["pohon_sono"]}, now=10.0)
    assert first["stability_status"] == "STABILIZING"
    current = first
    for index in range(1, 6):
        current = apply_stability_filter(session_id, {"tree_detected": True, "detected_classes": ["pohon_sono"]}, now=10.0 + index)
    assert current["stability_status"] == "STABLE_CANDIDATE_READY"
    assert current["latest_confirmed_result"]
