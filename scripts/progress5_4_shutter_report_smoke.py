from __future__ import annotations

import base64
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.progress5_4_field_runtime import PROGRESS5_4_REPORT_COLUMNS  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        app = create_app(runtime_root=Path(tmpdir))
        client = app.test_client()
        realtime = client.post("/api/field/realtime-frame", json={"point_id": "V001_pohon_sono", "timestamp_client_ms": 0}).get_json()
        shutter_no_gps = client.post(
            "/api/field/shutter-capture",
            json={"point_id": "V001_pohon_sono", "model_status": "MODEL_NOT_READY", "measurement_result": {}},
        ).get_json()
        shutter_gps = client.post(
            "/api/field/shutter-capture",
            json={
                "point_id": "V001_pohon_sono",
                "image_jpeg_base64": base64.b64encode(b"fake-jpeg-smoke").decode("ascii"),
                "gps_lat": -7.1,
                "gps_lon": 112.7,
                "gps_accuracy_m": 8,
                "gps_source": "GPS_SOURCE_BROWSER",
                "model_status": "MODEL_NOT_READY",
                "measurement_result": {"clearance_m": None, "reason_codes": ["INSUFFICIENT_DATA"]},
            },
        ).get_json()
    checks = {
        "realtime_no_autosave": realtime.get("no_autosave_on_realtime_frame") is True,
        "shutter_writes_report": shutter_gps.get("status") == "PROGRESS5_4_SHUTTER_REPORT_WRITTEN",
        "snapshot_runtime_only": shutter_gps.get("snapshot_status") == "SNAPSHOT_IMAGE_WRITTEN_RUNTIME_ONLY",
        "no_gps_no_marker": shutter_no_gps.get("map_status") == "NO_GPS_NO_MARKER",
        "gps_map_marker": shutter_gps.get("map_status") == "MAP_MARKER_WRITTEN",
        "schema_has_required_columns": bool(PROGRESS5_4_REPORT_COLUMNS),
        "google_sheets_local_ready": shutter_gps.get("google_sheets_status") == "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY",
    }
    passed = all(checks.values())
    return {"status": "PROGRESS5_4_SHUTTER_REPORT_SMOKE_PASS" if passed else "PROGRESS5_4_SHUTTER_REPORT_SMOKE_FAIL", "checks": checks}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
