from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PREFIXES = (
    "data/dataset_yolo/00_review_candidates/",
    "data/exports/",
    "data/raw/",
    "data/gps/",
    "data/processed/",
    "data/dataset_yolo/field_multiclass_v1/",
    "dataset_botol/",
    "results/",
    "runs/",
    "weights/",
    "models/",
)


def test_phase5_2_no_forbidden_label_or_training_paths_touched() -> None:
    completed = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert completed.returncode == 0
    for line in completed.stdout.splitlines():
        path = line[3:].replace("\\", "/")
        assert not any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES), line


def test_phase5_2_no_mobile_or_model_artifacts_created() -> None:
    for root in ["src", "scripts", "docs", "tests", "configs"]:
        for path in (ROOT / root).rglob("*"):
            if path.is_file():
                assert path.suffix.lower() not in {".apk", ".aab", ".pt", ".onnx", ".engine"}
