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
    routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
    required_routes = {
        "/",
        "/field-capture",
        "/api/network/health",
        "/api/network/whoami",
        "/api/latency/ping",
        "/api/runtime/status",
        "/api/runtime/public-links",
        "/api/model/status",
        "/api/calibration/status",
        "/api/realtime/frame",
        "/api/field/snapshot-report",
        "/api/field/manual-prediction",
        "/ws/realtime-detect",
    }
    required_ui = [
        "server-status",
        "model-status",
        "calibration-status",
        "realtime-transport-status",
        "secure-context-status",
        "gps-status",
        "camera-status",
        "tunnel-status",
        "manual-prediction",
        "snapshot-report",
        "copy-report-link",
        "open-map-report",
        "clearance_display_m_integer_floor",
        "MODEL_NOT_READY",
        "Advanced / Manual Provisional",
        "Mode utama Phase 16/Progress 5.2",
    ]
    checks = {
        "field_capture_http_200": client.get("/field-capture").status_code == 200,
        "all_required_routes_present": required_routes.issubset(routes),
        "ui_contract_tokens_present": all(token in html for token in required_ui),
        "runtime_public_links_json": client.get("/api/runtime/public-links").status_code == 200,
        "runtime_status_json": client.get("/api/runtime/status").status_code == 200,
        "hp_is_browser_not_mobile_app": "APK" not in html and "React Native" not in html and "Flutter" not in html,
    }
    passed = all(checks.values())
    return {"status": "PHASE5_2_UI_SMOKE_PASS" if passed else "PHASE5_2_UI_SMOKE_FAIL", "checks": checks}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
