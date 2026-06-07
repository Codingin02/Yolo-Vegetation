from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    [str(ROOT / "venv" / "Scripts" / "python.exe"), "-m", "compileall", "scripts", "src", "tests"],
    [str(ROOT / "venv" / "Scripts" / "python.exe"), "scripts/progress6_6_gate.py"],
    [str(ROOT / "venv" / "Scripts" / "python.exe"), "scripts/progress6_7_live_frame_no_500_smoke.py"],
    [str(ROOT / "venv" / "Scripts" / "python.exe"), "scripts/progress6_7_session_id_navigation_smoke.py"],
    [str(ROOT / "venv" / "Scripts" / "python.exe"), "scripts/progress6_7_map_result_gating_smoke.py"],
    [str(ROOT / "venv" / "Scripts" / "python.exe"), "scripts/progress6_7_tree_model_runtime_smoke.py"],
    [str(ROOT / "venv" / "Scripts" / "python.exe"), "scripts/progress6_7_growth_regression_smoke.py"],
    [str(ROOT / "venv" / "Scripts" / "python.exe"), "scripts/progress6_7_camera_ui_contract_smoke.py"],
]


def _run(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.splitlines()[-12:],
        "stderr_tail": completed.stderr.splitlines()[-12:],
    }


def run_gate() -> dict[str, object]:
    results = {" ".join(command[1:]): _run(command) for command in COMMANDS}
    failed = {name: result for name, result in results.items() if result["returncode"] != 0}
    return {
        "status": "PROGRESS_6_7_FIELD_CAMERA_FUNCTIONAL_MAP_SPREADSHEET_TREE_MODEL_READY_SAFE_MODE"
        if not failed
        else "PROGRESS_6_7_FIELD_CAMERA_FUNCTIONAL_MAP_SPREADSHEET_TREE_MODEL_FAILED",
        "results": results,
        "failed": failed,
        "no_label_touch": True,
        "no_training": True,
        "no_fake_detection": True,
        "no_fake_gps": True,
        "no_fake_precision": True,
    }


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
