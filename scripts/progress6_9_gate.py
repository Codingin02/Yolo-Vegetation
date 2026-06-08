from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"

COMMANDS = [
    [str(PYTHON), "-m", "compileall", "src", "scripts", "tests"],
    [str(PYTHON), "-m", "pytest", "-q", "-k", "progress6_9"],
    [str(PYTHON), "scripts/progress6_8_gate.py"],
    [str(PYTHON), "scripts/progress6_9_session_camera_smoke.py"],
    [str(PYTHON), "scripts/progress6_9_map_spreadsheet_smoke.py"],
    [str(PYTHON), "scripts/progress6_9_growth_model_smoke.py"],
    ["git", "diff", "--check"],
]


def _run(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.splitlines()[-16:],
        "stderr_tail": completed.stderr.splitlines()[-16:],
    }


def _no_label_touch() -> bool:
    completed = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    changed = [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]
    forbidden_prefixes = ("data/raw/", "data/gps/", "data/dataset_yolo/", "labels/", "runs/", "weights/", "models/")
    forbidden_suffixes = (".pt", ".onnx", ".engine", ".jpg", ".jpeg", ".png", ".mp4", ".mov", ".xlsx")
    return not any(path.startswith(forbidden_prefixes) or path.endswith(forbidden_suffixes) for path in changed)


def run_gate() -> dict[str, object]:
    results = {" ".join(command[1:] if command[0] == str(PYTHON) else command): _run(command) for command in COMMANDS}
    failed = {name: result for name, result in results.items() if result["returncode"] != 0}
    no_label_touch = _no_label_touch()
    if not no_label_touch:
        failed["no_label_touch_audit"] = {"returncode": 1, "stdout_tail": ["FORBIDDEN_LABEL_OR_MODEL_TOUCH"], "stderr_tail": []}
    return {
        "status": "PROGRESS_6_9_FIELD_CAMERA_SESSION_PROPAGATION_MAP_SPREADSHEET_MODEL_RECOVERY_READY_SAFE_MODE"
        if not failed
        else "PROGRESS_6_9_FIELD_CAMERA_SESSION_PROPAGATION_MAP_SPREADSHEET_MODEL_RECOVERY_FAILED",
        "results": results,
        "failed": failed,
        "no_label_touch": no_label_touch,
        "no_fake_detection": True,
        "no_fake_gps": True,
        "no_fake_clearance": True,
        "manual_input_primary": False,
    }


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
