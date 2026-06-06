from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_5_no_label_dataset_model_paths_in_git_changes() -> None:
    completed = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    forbidden_prefixes = (
        "data/raw/",
        "data/gps/",
        "data/processed/",
        "data/exports/",
        "data/dataset_yolo/",
        "dataset_botol/",
        "runs/",
        "models/",
        "weights/",
    )
    forbidden_suffixes = (".jpg", ".jpeg", ".png", ".mp4", ".mov", ".pt", ".onnx", ".engine", ".zip")
    for line in completed.stdout.splitlines():
        path = line[3:].replace("\\", "/")
        assert not path.startswith(forbidden_prefixes), line
        assert not path.lower().endswith(forbidden_suffixes), line
