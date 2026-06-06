from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.field_session_runtime import distance_reliability, gps_accuracy_status  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    close_base = {"latitude": -7.0, "longitude": 112.0, "accuracy": 12}
    close_current = {"latitude": -7.00001, "longitude": 112.0, "accuracy": 12}
    far_base = {"latitude": -7.0, "longitude": 112.0, "accuracy": 3}
    far_current = {"latitude": -7.001, "longitude": 112.0, "accuracy": 3}
    unreliable = distance_reliability(close_base, close_current)
    reliable = distance_reliability(far_base, far_current)
    checks = {
        "gps_good_threshold": gps_accuracy_status(5)["gps_accuracy_status"] == "GPS_ACCURACY_GOOD",
        "gps_medium_threshold": gps_accuracy_status(10)["gps_accuracy_status"] == "GPS_ACCURACY_MEDIUM",
        "gps_low_threshold": gps_accuracy_status(10.1)["gps_accuracy_status"] == "GPS_ACCURACY_LOW",
        "unreliable_when_accuracy_larger_than_distance": unreliable["distance_reliability_status"]
        == "GPS_ACCURACY_GREATER_THAN_DISTANCE",
        "reliable_when_distance_exceeds_accuracy": reliable["distance_reliability_status"]
        == "DISTANCE_REASONABLY_RELIABLE_FOR_FIELD_EVIDENCE",
    }
    status = "PROGRESS_6_2_GPS_POLICY_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_2_GPS_POLICY_SMOKE_FAIL"
    return {"status": status, "checks": checks, "unreliable": unreliable, "reliable": reliable}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
