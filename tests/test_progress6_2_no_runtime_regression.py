from __future__ import annotations

from ulp_project.progress6_2_training import progress6_2_gate_status


def test_progress6_2_gate_keeps_runtime_regression_flag_safe() -> None:
    result = progress6_2_gate_status()

    assert result["no_runtime_regression"] is True
    assert result["status"].startswith("PROGRESS_6_2_")
