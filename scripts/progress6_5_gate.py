from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

OLD_GATES = [
    "scripts/progress5_4_remote_https_camera_yolo_gate.py",
    "scripts/progress6_1_labeling_training_gate.py",
    "scripts/progress6_2_native_browser_gps_camera_gate.py",
    "scripts/progress6_3_field_acceptance_hardening_gate.py",
    "scripts/progress6_4_live_hp_acceptance_gate.py",
]

SMOKES = [
    "scripts/progress6_5_session_routes_smoke.py",
    "scripts/progress6_5_gps_truth_map_smoke.py",
    "scripts/progress6_5_shutter_idempotency_smoke.py",
    "scripts/progress6_5_mobile_ui_contract_smoke.py",
    "scripts/progress6_5_live_preflight.py",
]


def run_gate() -> dict[str, Any]:
    gate_results = {Path(script).name: _run(script) for script in OLD_GATES}
    smoke_results = {Path(script).name: _run(script) for script in SMOKES}
    failed = {
        **{name: result for name, result in gate_results.items() if result["returncode"] != 0},
        **{name: result for name, result in smoke_results.items() if result["returncode"] != 0},
    }
    status = (
        "PROGRESS_6_5_GPS_TRUTH_SESSION_CAMERA_UX_READY_MODEL_SAFE_MODE"
        if not failed
        else "PROGRESS_6_5_BLOCKED_VALIDATION_FAILED"
    )
    return {
        "status": status,
        "old_gates": gate_results,
        "smokes": smoke_results,
        "failed": failed,
        "no_label_touch": True,
        "no_model_touch": True,
        "no_training": True,
        "no_dataset_botol": True,
        "no_fake_gps": True,
        "no_fake_detection": True,
        "no_fake_precision": True,
    }


def _run(script: str) -> dict[str, Any]:
    completed = subprocess.run([sys.executable, script], cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
    }


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"] == "PROGRESS_6_5_GPS_TRUTH_SESSION_CAMERA_UX_READY_MODEL_SAFE_MODE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
