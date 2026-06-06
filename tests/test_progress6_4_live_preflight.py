from __future__ import annotations

from scripts.progress6_4_live_field_acceptance_preflight import build_preflight_status


def test_progress6_4_preflight_is_nonfatal_when_server_or_tunnel_absent() -> None:
    result = build_preflight_status(
        local_health_url="http://127.0.0.1:9/api/network/health",
        ngrok_api_url="http://127.0.0.1:9/api/tunnels",
        timeout=0.1,
    )
    assert result["status"] == "READY_FOR_LIVE_HP_TEST_SERVER_OR_TUNNEL_NOT_RUNNING"
    assert result["server_status"] == "SERVER_NOT_RUNNING"
    assert result["ngrok_status"] == "NGROK_NOT_RUNNING"
    assert result["server_command"].endswith("--host 0.0.0.0 --port 5000")
    assert result["ngrok_command"] == "ngrok http 5000"
