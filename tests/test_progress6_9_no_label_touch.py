from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_9_no_label_dataset_or_weight_touch() -> None:
    completed = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    changed = [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]
    forbidden_prefixes = ("data/raw/", "data/gps/", "data/dataset_yolo/", "labels/", "runs/", "weights/", "models/")
    forbidden_suffixes = (".pt", ".onnx", ".engine", ".jpg", ".jpeg", ".png", ".mp4", ".mov", ".xlsx")
    assert not [path for path in changed if path.startswith(forbidden_prefixes) or path.endswith(forbidden_suffixes)]
