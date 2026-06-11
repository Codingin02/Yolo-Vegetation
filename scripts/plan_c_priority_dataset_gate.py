from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_priority_dataset_gate import run_priority_dataset_gate  # noqa: E402


def main() -> int:
    staged = _staged_paths()
    result = run_priority_dataset_gate(staged_paths=staged)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _staged_paths() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
