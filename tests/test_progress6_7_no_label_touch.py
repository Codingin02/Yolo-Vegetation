from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_7_no_label_or_dataset_touch_in_new_scripts() -> None:
    scripts = sorted((ROOT / "scripts").glob("progress6_7_*.py"))
    assert scripts
    forbidden = ["data/dataset_yolo", "dataset_botol", "labels/", "runs/detect/train", "git add .", "git add -A"]
    for path in scripts:
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for token in forbidden:
            assert token not in text
