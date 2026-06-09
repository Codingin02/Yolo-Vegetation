from __future__ import annotations

import json

from progress6_21_canonical_output_smoke import run_smoke as run_canonical_smoke


def run_smoke() -> dict[str, object]:
    canonical = run_canonical_smoke()
    measurement = canonical.get("measurement_result") if isinstance(canonical.get("measurement_result"), dict) else {}
    checks = {
        "canonical_tree_detected": canonical.get("status") == "PROGRESS_6_21_CANONICAL_OUTPUT_PASS",
        "no_fake_pole": canonical.get("pole_detected") is False and canonical.get("pole_model_status") == "POLE_MODEL_NOT_READY",
        "no_fake_conductor": canonical.get("conductor_detected") is False and canonical.get("conductor_model_status") == "CONDUCTOR_MODEL_NOT_READY",
        "no_fake_flag": canonical.get("no_fake_pole_conductor_detection") is True,
        "no_fake_clearance": measurement.get("clearance_m") in {None, ""},
        "operator_clearance_not_final": measurement.get("zone_status") == "INSUFFICIENT_DATA",
    }
    return {
        "status": "PROGRESS_6_21_NO_FAKE_POLE_CONDUCTOR_PASS" if all(checks.values()) else "PROGRESS_6_21_NO_FAKE_POLE_CONDUCTOR_FAIL",
        "checks": checks,
        "canonical_status": canonical.get("status"),
        "measurement_result": measurement,
        "pole_detected": canonical.get("pole_detected"),
        "conductor_detected": canonical.get("conductor_detected"),
        "pole_model_status": canonical.get("pole_model_status"),
        "conductor_model_status": canonical.get("conductor_model_status"),
        "clearance_status": "CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR",
        "no_fake_detection": True,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
