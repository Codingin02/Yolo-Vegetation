from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"

COMMANDS = [
    [str(PYTHON), "-m", "compileall", "scripts", "src", "tests"],
    [str(PYTHON), "-m", "pytest"],
    [str(PYTHON), "scripts/progress6_7_gate.py"],
    [str(PYTHON), "scripts/progress6_8_route_registry_live_server_smoke.py"],
    [str(PYTHON), "scripts/progress6_8_no_degraded_camera_redirect_smoke.py"],
    [str(PYTHON), "scripts/progress6_8_browser_camera_permission_contract_smoke.py"],
    [str(PYTHON), "scripts/progress6_8_session_flow_hp_contract_smoke.py"],
    [str(PYTHON), "scripts/progress6_8_auto_yolo_geometry_contract_smoke.py"],
    [str(PYTHON), "scripts/progress6_8_stability_filter_smoke.py"],
]


def _run(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.splitlines()[-14:],
        "stderr_tail": completed.stderr.splitlines()[-14:],
    }


def run_gate() -> dict[str, object]:
    results = {" ".join(command[1:]): _run(command) for command in COMMANDS}
    failed = {name: result for name, result in results.items() if result["returncode"] != 0}
    return {
        "status": "PROGRESS_6_8_BROWSER_CAMERA_ROUTE_REGISTRY_AUTO_YOLO_GEOMETRY_READY_SAFE_MODE"
        if not failed
        else "PROGRESS_6_8_BROWSER_CAMERA_ROUTE_REGISTRY_AUTO_YOLO_GEOMETRY_FAILED",
        "results": results,
        "failed": failed,
        "no_training": True,
        "no_label_touch": True,
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
