from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_remote_realtime_server as remote_server


def test_progress6_8_route_registry_live_server_contains_session_routes(tmp_path) -> None:
    app = remote_server.create_app(runtime_root=tmp_path)
    client = app.test_client()
    payload = client.get("/api/runtime/route-registry").get_json()
    assert payload["status"] == "ROUTE_REGISTRY_READY"
    for route in [
        "/api/field/session/start",
        "/api/field/session/frame",
        "/api/field/session/gps-update",
        "/api/field/session/shutter",
        "/field-camera",
        "/field-map/session/<session_id>",
        "/field-spreadsheet/session/<session_id>",
    ]:
        assert payload["required_routes"][route] is True
