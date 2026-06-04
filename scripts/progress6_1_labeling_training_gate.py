from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_1_labeling import progress6_1_gate_status  # noqa: E402


FORBIDDEN_PREFIXES = (
    "data/raw/",
    "data/gps/",
    "data/processed/",
    "data/runtime/",
    "outputs/",
    "results/",
    "runs/",
    "models/",
    "weights/",
    "dataset_botol/",
)


def _no_forbidden_git_touch() -> bool:
    completed = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        return False
    for line in completed.stdout.splitlines():
        path = line[3:].replace("\\", "/")
        if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            return False
    return True


def main() -> int:
    result = progress6_1_gate_status()
    result["no_forbidden_git_touch"] = _no_forbidden_git_touch()
    if not result["no_forbidden_git_touch"]:
        result["status"] = "PROGRESS_6_1_BLOCKED_FORBIDDEN_GIT_TOUCH"
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].startswith("PROGRESS_6_1_") and "BLOCKED" not in result["status"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
