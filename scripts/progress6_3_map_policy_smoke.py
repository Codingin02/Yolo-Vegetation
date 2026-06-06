from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app


def run_smoke() -> dict[str, object]:
    with TemporaryDirectory() as tmp:
        app = create_app(runtime_root=Path(tmp))
        client = app.test_client()
        started = client.post("/api/field/session/start", json={"session_id": "MAP_SMOKE"}).get_json() or {}
        no_gps = client.get("/api/field/latest-map?session_id=MAP_SMOKE").get_json() or {}
        client.post(
            "/api/field/session/gps-update",
            json={
                "session_id": "MAP_SMOKE",
                "latitude": -7.123,
                "longitude": 110.456,
                "accuracy": 8,
            },
        )
        with_gps = client.get("/api/field/latest-map?session_id=MAP_SMOKE").get_json() or {}
    ok = (
        started.get("session_id") == "MAP_SMOKE"
        and no_gps.get("status") == "NO_GPS_NO_MARKER"
        and no_gps.get("map_exists") is True
        and with_gps.get("status") == "MAP_HTML_READY"
        and with_gps.get("google_maps_status") == "GOOGLE_MAPS_NOT_CONFIGURED"
    )
    return {
        "status": "PROGRESS_6_3_MAP_POLICY_SMOKE_PASS" if ok else "PROGRESS_6_3_MAP_POLICY_FAILED",
        "no_gps": no_gps,
        "with_gps": with_gps,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PROGRESS_6_3_MAP_POLICY_SMOKE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
