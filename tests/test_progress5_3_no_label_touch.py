from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PREFIXES = (
    "data/dataset_yolo/",
    "data/raw/",
    "data/gps/",
    "data/processed/",
    "data/exports/",
    "dataset_botol/",
    "results/",
    "runs/",
    "models/",
    "weights/",
)


def test_progress5_3_changes_do_not_touch_labeling_or_model_paths() -> None:
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


def test_progress5_3_no_mobile_app_artifacts_created() -> None:
    forbidden = {"react-native", "flutter", "apk", "pwa standalone"}
    touched = [
        ROOT / "src" / "ulp_project" / "templates" / "field_trial_checklist.html",
        ROOT / "src" / "ulp_project" / "field_trial_evidence.py",
        ROOT / "src" / "ulp_project" / "operator_failure_recovery.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in touched)
    assert not any(marker in combined for marker in forbidden)
