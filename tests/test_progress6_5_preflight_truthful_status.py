from __future__ import annotations

from scripts.progress6_5_live_preflight import _classify_public_route, classify_preflight


def test_progress6_5_preflight_separates_local_running_from_public_502() -> None:
    public_status = _classify_public_route({"ok": False, "http_status": 502, "error": "Bad Gateway"})
    status = classify_preflight("LOCAL_SERVER_RUNNING", "NGROK_RUNNING", public_status)
    assert public_status == "PUBLIC_ROUTE_BAD_GATEWAY"
    assert status == "PUBLIC_TUNNEL_TO_SERVER_MISMATCH"


def test_progress6_5_preflight_reports_ready_when_all_layers_are_ready() -> None:
    assert classify_preflight("LOCAL_SERVER_RUNNING", "NGROK_RUNNING", "PUBLIC_ROUTE_READY") == "LIVE_HP_TEST_READY"
