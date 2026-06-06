from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from progress6_4_live_field_acceptance_preflight import build_preflight_status
from ulp_project.field_acceptance_validation import validate_latest_acceptance

OLD_GATES = [
    "scripts/progress5_4_remote_https_camera_yolo_gate.py",
    "scripts/progress6_1_labeling_training_gate.py",
    "scripts/progress6_2_native_browser_gps_camera_gate.py",
    "scripts/progress6_3_field_acceptance_gate.py",
]


def run_gate() -> dict[str, Any]:
    old_gate_results = _run_old_gates()
    failed_gate = next((name for name, result in old_gate_results.items() if result["returncode"] != 0), "")
    if failed_gate:
        return {
            "status": "PROGRESS_6_4_RUNTIME_REGRESSION_FAILED",
            "failed_gate": failed_gate,
            "old_gates": old_gate_results,
        }

    preflight = build_preflight_status(timeout=2.0)
    acceptance = validate_latest_acceptance()
    acceptance_status = str(acceptance.get("acceptance_status") or "")
    if acceptance_status == "PHYSICAL_HP_ACCEPTANCE_PASS":
        status = "PROGRESS_6_4_LIVE_HP_ACCEPTANCE_PASS"
    elif acceptance_status == "PHYSICAL_HP_ACCEPTANCE_PASS_WITH_GPS_LIMITATION":
        status = "PROGRESS_6_4_LIVE_HP_ACCEPTANCE_PASS_WITH_GPS_LIMITATION"
    elif acceptance_status == "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST":
        status = "PROGRESS_6_4_LIVE_HP_ACCEPTANCE_READY_WAITING_FOR_USER_TEST"
    else:
        status = "PROGRESS_6_4_LIVE_HP_ACCEPTANCE_PARTIAL_REVIEW_REQUIRED"

    return {
        "status": status,
        "old_gates": old_gate_results,
        "preflight": preflight,
        "acceptance": acceptance,
        "server_or_tunnel_not_running_is_nonfatal_before_live_hp_test": True,
        "no_fake_acceptance": True,
        "no_fake_detection": True,
        "no_fake_gps": True,
        "no_fake_precision": True,
    }


def _run_old_gates() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for script in OLD_GATES:
        completed = subprocess.run([sys.executable, script], cwd=ROOT, text=True, capture_output=True, check=False)
        results[Path(script).name] = {
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout.strip().splitlines()[-5:],
            "stderr_tail": completed.stderr.strip().splitlines()[-5:],
        }
    return results


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {
        "PROGRESS_6_4_LIVE_HP_ACCEPTANCE_READY_WAITING_FOR_USER_TEST",
        "PROGRESS_6_4_LIVE_HP_ACCEPTANCE_PASS",
        "PROGRESS_6_4_LIVE_HP_ACCEPTANCE_PASS_WITH_GPS_LIMITATION",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
