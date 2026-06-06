from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)


SMOKES = [
    "scripts/progress6_3_status_consistency_audit.py",
    "scripts/progress6_3_physical_hp_acceptance_smoke.py",
    "scripts/progress6_3_gps_reliability_smoke.py",
    "scripts/progress6_3_visibility_policy_smoke.py",
    "scripts/progress6_3_report_result_smoke.py",
    "scripts/progress6_3_map_policy_smoke.py",
    "scripts/progress6_3_no_fake_precision_smoke.py",
]


def run_gate() -> dict[str, object]:
    results: dict[str, object] = {}
    for script in SMOKES:
        completed = subprocess.run([str(PYTHON), script], cwd=ROOT, text=True, capture_output=True, check=False)
        results[Path(script).name] = {
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout.strip().splitlines()[-3:],
            "stderr_tail": completed.stderr.strip().splitlines()[-3:],
        }
        if completed.returncode != 0:
            if "gps_reliability" in script:
                status = "PROGRESS_6_3_GPS_RELIABILITY_POLICY_FAILED"
            elif "status_consistency" in script:
                status = "PROGRESS_6_3_STATUS_CONSISTENCY_FAILED"
            else:
                status = "PROGRESS_6_3_RUNTIME_REGRESSION_FAILED"
            return {"status": status, "smokes": results}

    acceptance_pass = any(
        "PHYSICAL_HP_ACCEPTANCE_PASS" in "\n".join(value.get("stdout_tail", []))
        for value in results.values()
        if isinstance(value, dict)
    )
    return {
        "status": "PROGRESS_6_3_FIELD_ACCEPTANCE_PASS"
        if acceptance_pass
        else "PROGRESS_6_3_FIELD_ACCEPTANCE_HARDENING_READY_HP_PHYSICAL_TEST_PENDING",
        "smokes": results,
        "hp_physical_pass_requires_user_submitted_evidence": True,
        "no_fake_detection": True,
        "no_fake_gps": True,
    }


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {
        "PROGRESS_6_3_FIELD_ACCEPTANCE_PASS",
        "PROGRESS_6_3_FIELD_ACCEPTANCE_HARDENING_READY_HP_PHYSICAL_TEST_PENDING",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
