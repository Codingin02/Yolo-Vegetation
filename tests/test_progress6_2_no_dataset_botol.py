from __future__ import annotations

from ulp_project.progress6_1_labeling import build_training_command
from ulp_project.progress6_2_training import progress6_2_gate_status


def test_progress6_2_does_not_use_dataset_botol() -> None:
    command = " ".join(build_training_command())
    result = progress6_2_gate_status()

    assert "dataset_botol" not in command
    assert result["no_dataset_botol"] is True
