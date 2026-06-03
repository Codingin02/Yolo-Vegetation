from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from progress5_3_actual_runtime_smoke import build_smoke_status as build_actual_runtime_smoke  # noqa: E402
from progress5_3_hp_result_intake import build_smoke_status as build_hp_intake_smoke  # noqa: E402
from ulp_project.field_trial_diagnostics import collect_field_trial_diagnostics  # noqa: E402
from ulp_project.field_trial_evidence import build_field_trial_evidence_pack  # noqa: E402
from ulp_project.ngrok_runtime_probe import probe_ngrok_runtime  # noqa: E402
from ulp_project.operator_failure_recovery import build_failure_recovery  # noqa: E402


FORBIDDEN_PREFIXES = (
    "data/dataset_yolo/",
    "data\\dataset_yolo\\",
    "data/raw/",
    "data\\raw\\",
    "data/gps/",
    "data\\gps\\",
    "data/processed/",
    "data\\processed\\",
    "data/exports/",
    "data\\exports\\",
    "dataset_botol/",
    "results/",
    "runs/",
    "models/",
    "weights/",
)


def build_gate_status() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        evidence = build_field_trial_evidence_pack(evidence_dir=Path(tmpdir), dry_run=True)
    actual_runtime = build_actual_runtime_smoke()
    hp_intake = build_hp_intake_smoke()
    ngrok = probe_ngrok_runtime()
    diagnostics = collect_field_trial_diagnostics()
    recovery = build_failure_recovery(
        {
            "url_attempted": "http://localhost:5000/field-capture",
            "hp_can_open_url": False,
            "model_status": "MODEL_NOT_READY",
            "calibration_status": "CALIBRATION_NOT_READY",
        }
    )
    checks = {
        "actual_runtime_smoke": actual_runtime.get("status") == "PROGRESS5_3_ACTUAL_RUNTIME_SMOKE_PASS",
        "hp_result_intake_smoke": hp_intake.get("status") == "PROGRESS5_3_HP_RESULT_INTAKE_SMOKE_PASS",
        "evidence_pack_ready": evidence.get("status") == "FIELD_TRIAL_EVIDENCE_READY",
        "ngrok_probe_non_crashing": ngrok.get("status")
        in {"NGROK_HTTPS_TUNNEL_READY", "NGROK_RUNNING_NO_HTTPS_TUNNEL", "PUBLIC_TUNNEL_NOT_RUNNING", "NGROK_CLI_FOUND_BUT_TUNNEL_NOT_RUNNING", "NGROK_NOT_RUNNING"},
        "failure_recovery_ready": recovery.get("status") == "FAILURE_RECOVERY_DECISION_READY",
        "firewall_diagnostic_non_invasive": diagnostics.get("windows_firewall", {}).get("status") == "UNKNOWN_MANUAL_CHECK_REQUIRED",
        "hp_physical_test_not_overclaimed": evidence.get("hp_physical_confirmation_status") != "HP_CONFIRMED",
        "model_not_ready_safe_mode": evidence.get("model_status") == "MODEL_NOT_READY",
        "no_forbidden_git_touch": _no_forbidden_git_touch(),
    }
    passed = all(checks.values())
    status = (
        "PROGRESS_5_3_FIELD_TRIAL_EXECUTION_RECOVERY_READY_HP_PHYSICAL_TEST_PENDING"
        if passed
        else "PROGRESS_5_3_FIELD_TRIAL_EXECUTION_RECOVERY_BLOCKED"
    )
    return {
        "status": status,
        "checks": checks,
        "ngrok_status": ngrok.get("status"),
        "hp_physical_test_status": evidence.get("hp_physical_confirmation_status"),
        "evidence_status": evidence.get("status"),
        "failure_recovery": recovery,
        "windows_firewall": diagnostics.get("windows_firewall", {}),
        "operator_next": "ngrok http 5000",
    }


def _no_forbidden_git_touch() -> bool:
    completed = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        return False
    for line in completed.stdout.splitlines():
        path = line[3:] if len(line) > 3 else line
        normalized = path.replace("\\", "/")
        if any(normalized.startswith(prefix.replace("\\", "/")) for prefix in FORBIDDEN_PREFIXES):
            return False
    return True


def main() -> int:
    result = build_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PENDING") else 1


if __name__ == "__main__":
    raise SystemExit(main())
