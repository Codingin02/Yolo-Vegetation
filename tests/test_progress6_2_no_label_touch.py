from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PREFIXES = (
    "data/raw/",
    "data/gps/",
    "data/processed/",
    "data/exports/",
    "data/dataset_yolo/",
    "dataset_botol/",
    "outputs/",
    "results/",
    "runs/",
    "models/",
    "weights/",
)


def test_progress6_2_native_gps_changes_do_not_touch_label_or_runtime_data_paths() -> None:
    completed = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0
    for line in completed.stdout.splitlines():
        path = line[3:].replace("\\", "/")
        assert not any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES), line
