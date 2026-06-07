from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OLD_GATES = [
    "progress5_4_remote_https_camera_yolo_gate.py",
    "progress6_1_labeling_training_gate.py",
    "progress6_2_native_browser_gps_camera_gate.py",
    "progress6_3_field_acceptance_hardening_gate.py",
    "progress6_4_live_hp_acceptance_gate.py",
    "progress6_5_gate.py",
]

SMOKES = [
    "progress6_6_live_session_500_regression_smoke.py",
    "progress6_6_camera_first_ui_smoke.py",
    "progress6_6_growth_prior_smoke.py",
    "progress6_6_report_result_compact_smoke.py",
]


def _run(script: str) -> dict[str, object]:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-10:],
        "stderr_tail": completed.stderr.strip().splitlines()[-10:],
    }


def run_gate() -> dict[str, object]:
    old = {script: _run(script) for script in OLD_GATES}
    smokes = {script: _run(script) for script in SMOKES}
    failed = {script: result for script, result in {**old, **smokes}.items() if result["returncode"] != 0}
    status = "PROGRESS_6_6_CAMERA_FIRST_UI_AND_POHON_SONO_GROWTH_PRIOR_READY_MODEL_SAFE_MODE" if not failed else "PROGRESS_6_6_CAMERA_FIRST_UI_OR_GROWTH_PRIOR_GATE_FAILED"
    return {
        "status": status,
        "old_gates": old,
        "smokes": smokes,
        "failed": failed,
        "model_status": "MODEL_NOT_READY_SAFE_MODE",
        "no_training": True,
        "no_label_touch": True,
        "no_fake_detection": True,
        "no_fake_gps": True,
        "no_fake_precision": True,
        "growth_source_status": "PROXY_NOT_FIELD_OBSERVED",
    }


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"] == "PROGRESS_6_6_CAMERA_FIRST_UI_AND_POHON_SONO_GROWTH_PRIOR_READY_MODEL_SAFE_MODE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
