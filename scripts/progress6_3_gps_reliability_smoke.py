from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.gps_reliability_policy import distance_reliability, gps_accuracy_status


def run_smoke() -> dict[str, object]:
    low = gps_accuracy_status(11)
    medium = gps_accuracy_status(7)
    good = gps_accuracy_status(4)
    base = {"latitude": -7.0, "longitude": 110.0, "accuracy": 6}
    near = {"latitude": -7.0, "longitude": 110.00001, "accuracy": 6}
    far = {"latitude": -7.0, "longitude": 110.001, "accuracy": 5}
    unreliable = distance_reliability(base, near)
    reliable = distance_reliability(base, far)
    ok = (
        good["gps_accuracy_status"] == "GPS_ACCURACY_GOOD"
        and medium["gps_accuracy_status"] == "GPS_ACCURACY_MEDIUM"
        and low["gps_accuracy_status"] == "GPS_ACCURACY_LOW"
        and unreliable["is_distance_reliable"] is False
        and reliable["is_distance_reliable"] is True
    )
    return {
        "status": "PROGRESS_6_3_GPS_RELIABILITY_SMOKE_PASS" if ok else "PROGRESS_6_3_GPS_RELIABILITY_POLICY_FAILED",
        "good": good,
        "medium": medium,
        "low": low,
        "unreliable": unreliable,
        "reliable": reliable,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PROGRESS_6_3_GPS_RELIABILITY_SMOKE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
