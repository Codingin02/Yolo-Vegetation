from __future__ import annotations

from ulp_project.progress6_2_training import progress6_2_gate_status


def test_progress6_2_gate_reports_runtime_safe_mode_without_bestpt() -> None:
    result = progress6_2_gate_status()

    assert result["bestpt"]["runtime"]["do_not_commit_weights"] is True
    assert result["no_runtime_regression"] is True
    assert result["no_fake_detection"] is True
