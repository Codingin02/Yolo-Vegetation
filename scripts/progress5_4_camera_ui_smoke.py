from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    app = create_app()
    client = app.test_client()
    html = client.get("/field-capture").get_data(as_text=True)
    js = (ROOT / "src" / "ulp_project" / "static" / "field_capture.js").read_text(encoding="utf-8")
    routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
    required_routes = {
        "/api/field/realtime-status",
        "/api/field/realtime-frame",
        "/api/field/shutter-capture",
        "/api/field/latest-measurement",
        "/api/field/report-latest",
        "/api/field/map-latest",
        "/api/field/gps-status",
        "/api/field/calibration-status",
        "/api/field/debug-coco-frame",
    }
    required_ui = [
        "overlay-canvas",
        "shutter-capture",
        "Izinkan Kamera",
        "Izinkan GPS",
        "Mulai Deteksi",
        "Jepret / Shutter",
        "tree-height-m",
        "pole-height-reference-m",
        "cable-height-m",
        "zone_status",
        "Advanced Debug Only",
    ]
    checks = {
        "field_capture_200": client.get("/field-capture").status_code == 200,
        "required_routes": required_routes.issubset(routes),
        "required_ui": all(token in html for token in required_ui),
        "gps_background_watch_position": "watchPosition" in js,
        "shutter_endpoint_used": "/api/field/shutter-capture" in js,
        "realtime_endpoint_used": "/api/field/realtime-frame" in js,
        "primary_manual_clearance_removed": "Clearance (m)" not in html,
    }
    passed = all(checks.values())
    return {"status": "PROGRESS5_4_CAMERA_UI_SMOKE_PASS" if passed else "PROGRESS5_4_CAMERA_UI_SMOKE_FAIL", "checks": checks}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
