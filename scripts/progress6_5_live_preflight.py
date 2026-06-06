from __future__ import annotations

import argparse
import json
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SERVER_COMMAND = ".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000"
NGROK_COMMAND = "ngrok http 5000"


def build_preflight_status(
    *,
    local_health_url: str = "http://127.0.0.1:5000/api/network/health",
    ngrok_api_url: str = "http://127.0.0.1:4040/api/tunnels",
    retries: int = 3,
    timeout: float = 5.0,
) -> dict[str, Any]:
    local = _get_json(local_health_url, retries=retries, timeout=timeout)
    tunnels = _get_json(ngrok_api_url, retries=retries, timeout=timeout)
    public_url = _select_https_tunnel(tunnels.get("json") or {})
    public = _get_json(f"{public_url}/api/network/health", retries=1, timeout=timeout) if public_url else {"ok": False, "status": "PUBLIC_TUNNEL_NOT_RUNNING"}

    local_server_status = "LOCAL_SERVER_RUNNING" if local.get("ok") else "LOCAL_SERVER_NOT_RUNNING"
    ngrok_status = "NGROK_RUNNING" if public_url else "NGROK_NOT_RUNNING"
    public_route_status = _classify_public_route(public)
    status = classify_preflight(local_server_status, ngrok_status, public_route_status)

    return {
        "status": status,
        "local_server_status": local_server_status,
        "ngrok_status": ngrok_status,
        "public_route_status": public_route_status,
        "public_https_url": public_url,
        "public_field_capture_url": f"{public_url}/field-capture" if public_url else "",
        "public_field_acceptance_url": f"{public_url}/field-acceptance" if public_url else "",
        "local_probe": _compact_probe(local),
        "ngrok_probe": _compact_probe(tunnels),
        "public_probe": _compact_probe(public),
        "server_command": SERVER_COMMAND,
        "ngrok_command": NGROK_COMMAND,
        "nonfatal_for_code_validation": True,
    }


def classify_preflight(local_server_status: str, ngrok_status: str, public_route_status: str) -> str:
    if local_server_status == "LOCAL_SERVER_RUNNING" and ngrok_status == "NGROK_RUNNING" and public_route_status == "PUBLIC_ROUTE_READY":
        return "LIVE_HP_TEST_READY"
    if local_server_status == "LOCAL_SERVER_RUNNING" and ngrok_status == "NGROK_RUNNING" and public_route_status == "PUBLIC_ROUTE_BAD_GATEWAY":
        return "PUBLIC_TUNNEL_TO_SERVER_MISMATCH"
    if local_server_status == "LOCAL_SERVER_NOT_RUNNING" and ngrok_status == "NGROK_RUNNING":
        return "START_FLASK_SERVER_OR_CHECK_PORT_5000"
    return "READY_FOR_LIVE_HP_TEST_SERVER_OR_TUNNEL_NOT_RUNNING"


def _classify_public_route(result: dict[str, Any]) -> str:
    if result.get("ok"):
        return "PUBLIC_ROUTE_READY"
    if result.get("http_status") in {502, 503, 504}:
        return "PUBLIC_ROUTE_BAD_GATEWAY"
    error = str(result.get("error") or "").lower()
    if "timed out" in error or "timeout" in error:
        return "PUBLIC_ROUTE_TIMEOUT"
    if result.get("status") == "PUBLIC_TUNNEL_NOT_RUNNING":
        return "PUBLIC_TUNNEL_NOT_RUNNING"
    return "PUBLIC_ROUTE_NOT_READY"


def _get_json(url: str, *, retries: int, timeout: float) -> dict[str, Any]:
    result = _get_text(url, retries=retries, timeout=timeout)
    if not result.get("ok"):
        return result
    try:
        result["json"] = json.loads(str(result.get("text") or "{}"))
    except json.JSONDecodeError as exc:
        result["ok"] = False
        result["error"] = f"JSON_DECODE_FAILED:{exc.msg}"
    return result


def _get_text(url: str, *, retries: int, timeout: float) -> dict[str, Any]:
    last: dict[str, Any] = {"ok": False, "error": "NOT_ATTEMPTED"}
    for _ in range(max(1, retries)):
        request = urllib.request.Request(url, headers={"User-Agent": "ULP-Progress6.5-Preflight"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read(200_000).decode("utf-8", errors="replace")
                return {"ok": 200 <= response.status < 500, "http_status": response.status, "text": text}
        except urllib.error.HTTPError as exc:
            last = {"ok": 200 <= exc.code < 500, "http_status": exc.code, "error": str(exc)}
        except (OSError, socket.timeout) as exc:
            last = {"ok": False, "http_status": None, "error": str(exc)}
    return last


def _select_https_tunnel(payload: dict[str, Any]) -> str:
    for tunnel in payload.get("tunnels", []):
        public_url = str(tunnel.get("public_url") or "").rstrip("/")
        if public_url.startswith("https://"):
            return public_url
    return ""


def _compact_probe(probe: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(probe.get("ok")),
        "http_status": probe.get("http_status"),
        "error": str(probe.get("error") or "")[:180],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Progress 6.5 truthful live server/tunnel preflight.")
    parser.add_argument("--live", action="store_true", help="Return non-zero unless LIVE_HP_TEST_READY.")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    result = build_preflight_status(timeout=args.timeout, retries=args.retries)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    if args.live and result["status"] != "LIVE_HP_TEST_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
