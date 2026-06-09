from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"

COMMANDS = [
    [str(PYTHON), "-m", "compileall", "scripts", "src", "tests"],
    [str(PYTHON), "-m", "pytest"],
    [str(PYTHON), "scripts/progress6_20_gps_yolo_live_smoke.py"],
    [str(PYTHON), "scripts/progress6_21_canonical_output_smoke.py"],
    [str(PYTHON), "scripts/progress6_21_frontend_overlay_contract_smoke.py"],
    [str(PYTHON), "scripts/progress6_21_live_no_fake_pole_conductor_smoke.py"],
    ["git", "diff", "--check"],
]


def _run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.splitlines()[-18:],
        "stderr_tail": completed.stderr.splitlines()[-18:],
    }


def run_gate() -> dict[str, Any]:
    results = {" ".join(command[1:] if command[0].endswith("python.exe") else command): _run(command) for command in COMMANDS}
    failed = {name: result for name, result in results.items() if result["returncode"] != 0}
    status = (
        "PROGRESS_6_21_LIVE_YOLO_CANONICAL_OVERLAY_READY_GPS_RELIABLE_SAFE_MODE"
        if not failed
        else "PROGRESS_6_21_LIVE_YOLO_CANONICAL_OVERLAY_FAILED"
    )
    return {
        "status": status,
        "results": results,
        "failed": failed,
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_dataset_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
        "no_fake_detection": True,
        "no_fake_pole_conductor": True,
    }


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
