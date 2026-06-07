from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_6_no_label_touch() -> None:
    completed = subprocess.run(["git", "diff", "--name-only"], cwd=ROOT, text=True, capture_output=True, check=False)
    forbidden_prefixes = (
        "data/dataset_yolo/",
        "data/raw/",
        "data/gps/",
        "runs/",
        "models/",
        "weights/",
        "dataset_botol/",
    )
    changed = [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]
    assert not [path for path in changed if path.startswith(forbidden_prefixes)]
