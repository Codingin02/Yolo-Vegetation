from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_2_training import progress6_2_training_policy_status


def test_progress6_2_training_not_run_without_data_yaml(tmp_path: Path) -> None:
    result = progress6_2_training_policy_status(tmp_path / "missing.yaml")

    assert result["status"] == "TRAINING_NOT_RUN_DATASET_NOT_READY"
    assert result["training_executed"] is False
    assert result["no_fake_accuracy"] is True
