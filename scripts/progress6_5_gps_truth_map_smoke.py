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
        client.post(
            "/api/field/session/start",
            json={
                "session_id": "P65_MAP_SESSION",
                "source_mode": "SMOKE_TEST",
                "base_gps": {"latitude": -7.1, "longitude": 112.7, "accuracy": 8, "source": "GPS_SOURCE_BROWSER"},
            },
        )
        rounded = client.get("/api/field/latest-map?session_id=P65_MAP_SESSION").get_json() or {}
        client.post(
            "/api/field/session/gps-update",
            json={
                "session_id": "P65_MAP_SESSION",
                "latitude": -7.1234567,
                "longitude": 112.7654321,
                "accuracy": 7,
                "source": "GPS_SOURCE_BROWSER",
            },
        )
        valid = client.get("/api/field/latest-map?session_id=P65_MAP_SESSION").get_json() or {}
        html = client.get("/field-map/session/P65_MAP_SESSION").get_data(as_text=True)
        no_gps = client.get("/api/field/latest-map?session_id=P65_NO_GPS").get_json() or {}
    checks = {
        "rounded_coordinate_no_marker": rounded.get("status") == "NO_GPS_NO_MARKER"
        and rounded.get("gps_precision_status") == "GPS_PRECISION_LOST_ROUNDED_COORDINATE",
        "valid_session_map_ready": valid.get("status") == "MAP_HTML_READY"
        and valid.get("field_map_url") == "/field-map/session/P65_MAP_SESSION",
        "raw_precision_preserved": "-7.1234567" in html and "112.7654321" in html,
        "no_default_coordinate": "-7.1000000" not in html and "112.7000000" not in html,
        "no_marker_without_valid_gps": no_gps.get("status") == "NO_GPS_NO_MARKER",
        "no_stale_global_map": "progress5_4_fallback" not in json.dumps(valid),
    }
    return {
        "status": "PROGRESS_6_5_GPS_TRUTH_MAP_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_5_GPS_TRUTH_MAP_SMOKE_FAIL",
        "checks": checks,
        "rounded": rounded,
        "valid": valid,
        "no_gps": no_gps,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
