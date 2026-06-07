from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_remote_realtime_server as remote_server  # noqa: E402

REQUIRED = {
    "/api/field/session/start": "POST",
    "/api/field/session/frame": "POST",
    "/api/field/session/gps-update": "POST",
    "/api/field/session/shutter": "POST",
    "/field-camera": "GET",
    "/field-capture": "GET",
    "/field-map/session/<session_id>": "GET",
    "/field-spreadsheet/session/<session_id>": "GET",
}


def run_smoke() -> dict[str, object]:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        app = remote_server.create_app(runtime_root=Path(tmp))
        route_methods: dict[str, set[str]] = {}
        for rule in app.url_map.iter_rules():
            route_methods.setdefault(rule.rule, set()).update(rule.methods)
        registry_checks = {route: method in route_methods.get(route, set()) for route, method in REQUIRED.items()}
        client = app.test_client()
        registry = client.get("/api/runtime/route-registry")
        start = client.post(
            "/api/field/session/start",
            json={
                "point_id": "V001_pohon_sono",
                "idempotency_key": "P68_ROUTE_REGISTRY",
                "secure_context_status": "SECURE_CONTEXT_OK",
                "current_url_mode": "HTTPS_PUBLIC_READY",
            },
        )
        session_id = (start.get_json() or {}).get("session_id")
        frame = client.post("/api/field/session/frame", json={"session_id": session_id, "frame_image_base64": "invalid"})
        gps = client.post(
            "/api/field/session/gps-update",
            json={"session_id": session_id, "latitude": -7.2161234, "longitude": 112.7351234, "accuracy": 6.7, "source": "browser_watchPosition"},
        )
        shutter = client.post("/api/field/session/shutter", json={"session_id": session_id, "idempotency_key": "P68_SHUTTER"})
        map_page = client.get(f"/field-map/session/{session_id}")
        sheet_page = client.get(f"/field-spreadsheet/session/{session_id}")
        map_page.get_data()
        sheet_page.get_data()
        no_bad_codes = all(response.status_code not in {404, 405, 500} for response in [registry, start, frame, gps, shutter, map_page, sheet_page])
        checks = {
            "server_script_create_app_available": callable(remote_server.create_app),
            "required_routes_registered": all(registry_checks.values()),
            "route_registry_endpoint_ready": registry.status_code == 200 and (registry.get_json() or {}).get("status") == "ROUTE_REGISTRY_READY",
            "start_no_404_405_500": start.status_code not in {404, 405, 500},
            "frame_no_404_405_500": frame.status_code not in {404, 405, 500},
            "gps_no_404_405_500": gps.status_code not in {404, 405, 500},
            "shutter_no_404_405_500": shutter.status_code not in {404, 405, 500},
            "map_html_no_404_405_500": map_page.status_code not in {404, 405, 500},
            "spreadsheet_no_404_405_500": sheet_page.status_code not in {404, 405, 500},
            "session_id_normal": isinstance(session_id, str) and session_id.startswith("FS_") and not session_id.startswith("FS_DEGRADED"),
            "all_live_flow_codes_safe": no_bad_codes,
        }
    return {
        "status": "PROGRESS_6_8_ROUTE_REGISTRY_LIVE_SERVER_PASS" if all(checks.values()) else "PROGRESS_6_8_ROUTE_REGISTRY_LIVE_SERVER_FAIL",
        "checks": checks,
        "registry_checks": registry_checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
