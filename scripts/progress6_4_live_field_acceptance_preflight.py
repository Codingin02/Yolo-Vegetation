from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SERVER_COMMAND = ".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000"
NGROK_COMMAND = "ngrok http 5000"
PUBLIC_ROUTES = ["/field-capture", "/field-acceptance", "/field-report", "/field-result", "/field-manual-input"]


def build_preflight_status(
    *,
    local_health_url: str = "http://127.0.0.1:5000/api/network/health",
    ngrok_api_url: str = "http://127.0.0.1:4040/api/tunnels",
    timeout: float = 2.0,
) -> dict[str, Any]:
    server_probe = _get_json(local_health_url, timeout=timeout)
    tunnel_probe = _get_json(ngrok_api_url, timeout=timeout)
    public_url = _select_https_tunnel(tunnel_probe.get("json") or {})
    route_status = _public_route_status(public_url, timeout=timeout) if public_url else {}

    server_status = "SERVER_RUNNING" if server_probe["ok"] else "SERVER_NOT_RUNNING"
    ngrok_status = "NGROK_RUNNING" if public_url else "NGROK_NOT_RUNNING"
    public_url_status = "PUBLIC_HTTPS_URL_READY" if public_url else "PUBLIC_TUNNEL_NOT_RUNNING"
    hp_ready = server_status == "SERVER_RUNNING" and ngrok_status == "NGROK_RUNNING" and bool(public_url)
    hp_test_status = "HP_TEST_READY" if hp_ready else "HP_TEST_BLOCKED_SERVER_OR_TUNNEL_NOT_RUNNING"
    code_validation_status = "HP_TEST_READY" if hp_ready else "READY_FOR_LIVE_HP_TEST_SERVER_OR_TUNNEL_NOT_RUNNING"
    return {
        "status": code_validation_status,
        "server_status": server_status,
        "ngrok_status": ngrok_status,
        "public_url_status": public_url_status,
        "hp_test_status": hp_test_status,
        "public_https_url": public_url or "",
        "public_field_capture_url": f"{public_url}/field-capture" if public_url else "",
        "public_field_acceptance_url": f"{public_url}/field-acceptance" if public_url else "",
        "route_status": route_status,
        "server_command": SERVER_COMMAND,
        "ngrok_command": NGROK_COMMAND,
        "server_probe_error": server_probe.get("error", ""),
        "ngrok_probe_error": tunnel_probe.get("error", ""),
        "preflight_is_nonfatal_without_live_server": True,
    }


def _public_route_status(public_url: str, *, timeout: float) -> dict[str, Any]:
    status: dict[str, Any] = {}
    for route in PUBLIC_ROUTES:
        result = _get_text(f"{public_url}{route}", timeout=timeout)
        status[route] = {
            "status": "PUBLIC_ROUTE_REACHABLE" if result["ok"] else "PUBLIC_ROUTE_NOT_REACHABLE",
            "http_status": result.get("http_status"),
            "error": result.get("error", ""),
        }
    return status


def _get_json(url: str, *, timeout: float) -> dict[str, Any]:
    result = _get_text(url, timeout=timeout)
    if not result["ok"]:
        return result
    try:
        result["json"] = json.loads(str(result.get("text") or "{}"))
    except json.JSONDecodeError as exc:
        result["ok"] = False
        result["error"] = f"JSON_DECODE_FAILED:{exc.msg}"
    return result


def _get_text(url: str, *, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "ULP-Progress6.4-Preflight"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read(200_000).decode("utf-8", errors="replace")
            return {"ok": 200 <= response.status < 500, "http_status": response.status, "text": text}
    except urllib.error.HTTPError as exc:
        return {"ok": 200 <= exc.code < 500, "http_status": exc.code, "error": str(exc)}
    except OSError as exc:
        return {"ok": False, "http_status": None, "error": str(exc)}


def _select_https_tunnel(payload: dict[str, Any]) -> str:
    for tunnel in payload.get("tunnels", []):
        public_url = str(tunnel.get("public_url") or "").rstrip("/")
        if public_url.startswith("https://"):
            return public_url
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Progress 6.4 live HP acceptance preflight.")
    parser.add_argument("--live", action="store_true", help="Return non-zero when server/tunnel is not running.")
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()
    result = build_preflight_status(timeout=args.timeout)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.live and result["hp_test_status"] != "HP_TEST_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
