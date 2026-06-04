from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_1_labeling import SEED, build_training_command, training_plan


def test_progress6_1_training_command_has_required_defaults() -> None:
    command = build_training_command(data_yaml=Path("data/dataset_yolo/field_multiclass_v1/data.yaml"))
    joined = " ".join(command)

    assert "yolov8n.pt" in joined
    assert "epochs=50" in joined
    assert "imgsz=640" in joined
    assert f"seed={SEED}" in joined
    assert "project=runs/field_multiclass" in joined


def test_progress6_1_training_plan_skips_missing_dataset(tmp_path: Path) -> None:
    plan = training_plan(data_yaml=tmp_path / "missing" / "data.yaml")

    assert plan["status"] == "TRAINING_NOT_RUN_DATASET_NOT_READY"
    assert plan["no_fake_accuracy"] is True
