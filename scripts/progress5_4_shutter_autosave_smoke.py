from __future__ import annotations

import base64
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
        before = client.get("/api/field/latest-report").get_json()
        realtime = client.post("/api/field/realtime-frame", json={"point_id": "V001_pohon_sono", "timestamp_client_ms": 0}).get_json()
        shutter = client.post(
            "/api/field/shutter-capture",
            json={
                "point_id": "V001_pohon_sono",
                "operator_name": "operator-smoke",
                "image_jpeg_base64": base64.b64encode(b"progress54-shutter").decode("ascii"),
                "gps_lat": -7.1,
                "gps_lon": 112.7,
                "gps_accuracy_m": 9,
                "gps_source": "GPS_SOURCE_BROWSER",
                "secure_context_status": "SECURE_CONTEXT_OK",
                "current_url_mode": "HTTPS_PUBLIC_READY",
                "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
                "model_status": "MODEL_NOT_READY",
                "measurement_result": {"reason_codes": ["MODEL_NOT_READY"]},
                "notes": "autosave smoke",
            },
        ).get_json()
    checks = {
        "latest_report_endpoint_exists": before.get("status") is not None,
        "realtime_does_not_autosave": realtime.get("no_autosave_on_realtime_frame") is True,
        "shutter_writes_csv": shutter.get("status") == "PROGRESS5_4_SHUTTER_REPORT_WRITTEN",
        "csv_autosave_name": str(shutter.get("report_csv_url", "")).endswith("field_capture_autosave.csv"),
        "google_sheets_local_ready": shutter.get("google_sheets_status") == "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY",
        "map_marker_with_gps": shutter.get("map_status") == "MAP_MARKER_WRITTEN",
    }
    status = "PROGRESS5_4_SHUTTER_AUTOSAVE_SMOKE_PASS" if all(checks.values()) else "PROGRESS5_4_SHUTTER_AUTOSAVE_SMOKE_FAIL"
    return {"status": status, "checks": checks, "shutter": {k: shutter.get(k) for k in ("report_id", "report_csv_url", "map_url", "map_status")}}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
