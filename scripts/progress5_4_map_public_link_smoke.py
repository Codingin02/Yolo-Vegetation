from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        client = create_app(runtime_root=Path(tmpdir)).test_client()
        no_gps = client.post("/api/field/shutter-capture", json={"point_id": "V001_pohon_sono", "model_status": "MODEL_NOT_READY"}).get_json()
        with_gps = client.post(
            "/api/field/shutter-capture",
            json={"point_id": "V001_pohon_sono", "gps_lat": -7.1, "gps_lon": 112.7, "gps_accuracy_m": 8, "gps_source": "GPS_SOURCE_BROWSER", "model_status": "MODEL_NOT_READY"},
        ).get_json()
        map_response_code = client.get(with_gps.get("map_url") or "/api/field/latest-map").status_code
    checks = {
        "no_gps_no_marker": no_gps.get("map_status") == "NO_GPS_NO_MARKER",
        "gps_marker_written": with_gps.get("map_status") == "MAP_MARKER_WRITTEN",
        "map_link_served": map_response_code == 200,
        "map_url_relative_for_public_tunnel": str(with_gps.get("map_url", "")).startswith("/field-maps/"),
    }
    status = "PROGRESS5_4_MAP_PUBLIC_LINK_SMOKE_PASS" if all(checks.values()) else "PROGRESS5_4_MAP_PUBLIC_LINK_SMOKE_FAIL"
    return {"status": status, "checks": checks, "map_url": with_gps.get("map_url")}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
