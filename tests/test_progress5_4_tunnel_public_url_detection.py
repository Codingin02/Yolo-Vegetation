from __future__ import annotations

from ulp_project import runtime_links


def test_progress5_4_public_links_use_ngrok_https_when_probe_finds_tunnel(monkeypatch) -> None:
    def fake_probe(*args, **kwargs):
        return {
            "status": "NGROK_HTTPS_TUNNEL_READY",
            "public_https_url": "https://lend-trunks-unpaid.ngrok-free.dev",
            "public_field_capture_url": "https://lend-trunks-unpaid.ngrok-free.dev/field-capture",
        }

    monkeypatch.setattr(runtime_links, "probe_ngrok_runtime", fake_probe)

    links = runtime_links.build_public_links(port=5000)

    assert links["status"] == "READY"
    assert links["public_url_status"] == "PUBLIC_HTTPS_TUNNEL_READY"
    assert links["tunnel_status"] == "NGROK_HTTPS_TUNNEL_READY"
    assert links["public_field_capture_url"] == "https://lend-trunks-unpaid.ngrok-free.dev/field-capture"
