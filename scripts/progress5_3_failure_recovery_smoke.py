from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.operator_failure_recovery import build_failure_recovery  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    cases = {
        "localhost_wrong_on_hp": build_failure_recovery({"url_attempted": "http://localhost:5000/field-capture", "hp_can_open_url": False}),
        "camera_insecure": build_failure_recovery({"hp_can_open_url": True, "camera_status": "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT"}),
        "gps_denied": build_failure_recovery({"hp_can_open_url": True, "gps_status": "GPS_PERMISSION_DENIED"}),
        "model_not_ready": build_failure_recovery({"hp_can_open_url": True, "model_status": "MODEL_NOT_READY", "calibration_status": "CALIBRATION_READY"}),
    }
    checks = {
        "localhost_mapping_ready": "localhost" in cases["localhost_wrong_on_hp"]["likely_cause"].lower(),
        "camera_mapping_ready": cases["camera_insecure"]["severity"] == "MEDIUM",
        "gps_mapping_ready": cases["gps_denied"]["severity"] == "MEDIUM",
        "model_safe_mode_mapping_ready": cases["model_not_ready"]["severity"] == "INFO",
    }
    passed = all(checks.values())
    return {
        "status": "PROGRESS5_3_FAILURE_RECOVERY_SMOKE_PASS" if passed else "PROGRESS5_3_FAILURE_RECOVERY_SMOKE_FAIL",
        "checks": checks,
        "cases": cases,
    }


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
