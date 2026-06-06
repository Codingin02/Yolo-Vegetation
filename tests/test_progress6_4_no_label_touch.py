from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_4_new_code_does_not_touch_label_or_model_data_paths() -> None:
    paths = [
        ROOT / "scripts" / "progress6_4_live_field_acceptance_preflight.py",
        ROOT / "scripts" / "progress6_4_print_live_hp_test_commands.py",
        ROOT / "scripts" / "progress6_4_acceptance_evidence_validator.py",
        ROOT / "scripts" / "progress6_4_live_hp_acceptance_gate.py",
        ROOT / "src" / "ulp_project" / "field_acceptance_validation.py",
    ]
    forbidden = ["data/dataset_yolo", "dataset_botol", "runs/", "weights/", "models/", ".pt"]
    for path in paths:
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for token in forbidden:
            assert token not in text
