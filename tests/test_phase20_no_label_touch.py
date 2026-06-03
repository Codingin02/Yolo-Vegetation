from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_new_source_references_label_touch_modes():
    forbidden = ["import_makesense_yolo_export.py --mode copy", "build_field_multiclass_dataset.py --mode build"]
    phase_files = [
        ROOT / "docs" / "PHASE17_20_FINAL_SYSTEM_COMPLETION_REPORT.md",
        ROOT / "docs" / "FIELD_TRIAL_QUICKSTART_HP_TO_LAPTOP.md",
        ROOT / "docs" / "FINAL_OPERATOR_COMMAND_SEQUENCE.md",
        ROOT / "scripts" / "phase17_20_final_system_completion_gate.py",
        ROOT / "scripts" / "run_field_trial_operator.py",
    ]
    for path in phase_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not any(item in text for item in forbidden)
