from pathlib import Path

from scripts.phase6_mobile_environmental_gate import build_phase6_gate_status


def test_phase6_gate_ready_waiting_for_labels_and_model():
    result = build_phase6_gate_status(Path.cwd())
    assert result["overall_status"] == "PHASE6_SYSTEM_READY_WAITING_FOR_LABELS_AND_MODEL"
    assert result["model_status"] == "MODEL_NOT_READY"
    assert result["mobile_runtime_status"] == "FIELD_CAPTURE_BROWSER_READY_MODEL_NOT_READY"


def test_dataset_botol_is_not_main_dataset_path():
    config = Path("configs/project_paths.yaml").read_text(encoding="utf-8")
    assert "field_multiclass_v1" in config
    assert "dataset_botol" not in config
