from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_8_new_files_do_not_touch_label_or_training_data() -> None:
    paths = list((ROOT / "scripts").glob("progress6_8_*.py"))
    paths += [
        ROOT / "src" / "ulp_project" / "realtime_yolo_detection_pipeline.py",
        ROOT / "src" / "ulp_project" / "geometry_reference_scaling.py",
        ROOT / "src" / "ulp_project" / "realtime_stability_filter.py",
    ]
    forbidden = ["data/dataset_yolo", "dataset_botol", "labels/", "git add .", "git add -A"]
    for path in paths:
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for token in forbidden:
            assert token not in text
