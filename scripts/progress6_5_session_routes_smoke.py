from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def run_smoke() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        client = create_app(runtime_root=Path(tmpdir)).test_client()
        start = client.post("/api/field/session/start", json={"source_mode": "SMOKE_TEST"}).get_json() or {}
        shutter = client.post(
            "/api/field/session/shutter",
            json={"source_mode": "SMOKE_TEST", "idempotency_key": "P65_SESSION_ROUTE_SMOKE"},
        ).get_json() or {}
        stop = client.post("/api/field/session/stop", json={}).get_json() or {}
    checks = {
        "session_start_no_500": start.get("status") == "FIELD_SESSION_STARTED",
        "session_shutter_no_500": shutter.get("status") in {"FIELD_SESSION_SHUTTER_SAVED", "DUPLICATE_SHUTTER_IGNORED"},
        "session_stop_no_500": stop.get("status") in {"FIELD_SESSION_STOPPED", "NO_ACTIVE_SESSION_TO_STOP"},
        "no_fake_detection": start.get("no_fake_detection") is True and shutter.get("no_fake_detection") is True,
    }
    return {
        "status": "PROGRESS_6_5_SESSION_ROUTES_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_5_SESSION_ROUTES_SMOKE_FAIL",
        "checks": checks,
        "start": start,
        "shutter": shutter,
        "stop": stop,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
