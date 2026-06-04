from __future__ import annotations

from ulp_project import field_capture_routes, runtime_links
from ulp_project.flask_app import create_app


def test_progress5_4_runtime_status_syncs_with_tunnel_status(monkeypatch) -> None:
    def fake_probe(*args, **kwargs):
        return {
            "status": "NGROK_HTTPS_TUNNEL_READY",
            "public_https_url": "https://lend-trunks-unpaid.ngrok-free.dev",
            "field_capture_public_url": "https://lend-trunks-unpaid.ngrok-free.dev/field-capture",
            "public_field_capture_url": "https://lend-trunks-unpaid.ngrok-free.dev/field-capture",
        }

    monkeypatch.setattr(runtime_links, "probe_ngrok_runtime", fake_probe)
    monkeypatch.setattr(field_capture_routes, "probe_ngrok_runtime", fake_probe)
    client = create_app().test_client()

    tunnel = client.get("/api/runtime/tunnel-status").get_json()
    runtime = client.get("/api/runtime/status").get_json()

    assert tunnel["status"] == "NGROK_HTTPS_TUNNEL_READY"
    assert runtime["tunnel_status"] == "NGROK_HTTPS_TUNNEL_READY"
    assert runtime["public_links"]["status"] != "NO_PUBLIC_TUNNEL_CONFIGURED"
    assert runtime["public_links"]["public_field_capture_url"].startswith("https://")
