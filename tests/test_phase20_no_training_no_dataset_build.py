from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_training_actual_or_dataset_botol_main_in_new_runtime():
    targets = [
        ROOT / "src" / "ulp_project" / "model_handoff.py",
        ROOT / "src" / "ulp_project" / "realtime_inference_contract.py",
        ROOT / "src" / "ulp_project" / "runtime_diagnostics.py",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "dataset_botol" not in text
        assert "train(" not in text
