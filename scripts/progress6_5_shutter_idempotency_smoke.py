from __future__ import annotations

import csv
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.field_session_runtime import PROGRESS5_4_REPORT_CSV, SESSION_SMOKE_REPORT_CSV  # noqa: E402


def run_smoke() -> dict[str, object]:
    key = f"P65_IDEMPOTENCY_{int(time.time() * 1000)}"
    with tempfile.TemporaryDirectory() as tmpdir:
        client = create_app(runtime_root=Path(tmpdir)).test_client()
        start = client.post(
            "/api/field/session/start",
            json={
                "session_id": f"P65_IDEMPOTENCY_{int(time.time())}",
                "source_mode": "SMOKE_TEST",
                "operator_name": "operator-smoke",
                "base_gps": {"latitude": -7.1234567, "longitude": 112.7654321, "accuracy": 8, "source": "GPS_SOURCE_BROWSER"},
            },
        ).get_json() or {}
        payload = {
            "session_id": start.get("session_id"),
            "source_mode": "SMOKE_TEST",
            "idempotency_key": key,
            "current_gps": {"latitude": -7.1234567, "longitude": 112.7654321, "accuracy": 8, "source": "GPS_SOURCE_BROWSER"},
        }
        first = client.post("/api/field/session/shutter", json=payload).get_json() or {}
        second = client.post("/api/field/session/shutter", json=payload).get_json() or {}

    smoke_rows = _count_key(SESSION_SMOKE_REPORT_CSV, key)
    live_rows = _count_key(PROGRESS5_4_REPORT_CSV, key)
    checks = {
        "first_csv_appended": first.get("csv_appended") is True,
        "second_duplicate_ignored": second.get("status") == "DUPLICATE_SHUTTER_IGNORED"
        and second.get("csv_appended") is False
        and second.get("duplicate_ignored") is True,
        "smoke_csv_single_row": smoke_rows == 1,
        "smoke_not_in_live_csv": live_rows == 0,
    }
    return {
        "status": "PROGRESS_6_5_SHUTTER_IDEMPOTENCY_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_5_SHUTTER_IDEMPOTENCY_SMOKE_FAIL",
        "checks": checks,
        "idempotency_key": key,
        "first": first,
        "second": second,
        "smoke_rows": smoke_rows,
        "live_rows": live_rows,
    }


def _count_key(path: Path, key: str) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for row in csv.DictReader(handle) if row.get("idempotency_key") == key)


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
