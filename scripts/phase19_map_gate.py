from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.map_report_policy import should_create_map_marker  # noqa: E402


def main() -> int:
    no_gps = should_create_map_marker({"point_id": "V001"})
    with_gps = should_create_map_marker({"latitude": -7.0, "longitude": 112.0, "risk_priority": "CRITICAL"})
    checks = {"no_gps_no_marker": no_gps["write_marker"] is False, "gps_marker_allowed": with_gps["write_marker"] is True and with_gps["color"] == "red"}
    status = "PHASE19_MAP_GATE_READY" if all(checks.values()) else "PHASE19_MAP_GATE_FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2, ensure_ascii=False))
    print(status)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
