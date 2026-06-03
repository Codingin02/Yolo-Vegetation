"""Runtime ngrok probe for Progress 5.3 field-trial evidence."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any, Callable


NGROK_API_URL = "http://127.0.0.1:4040/api/tunnels"


def probe_ngrok_runtime(
    port: int = 5000,
    *,
    timeout_s: float = 1.5,
    which_func: Callable[[str], str | None] | None = None,
    process_checker: Callable[[], str] | None = None,
    urlopen_func: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Probe local ngrok runtime without tokens or automatic tunnel creation."""

    which = which_func or shutil.which
    process_status = process_checker() if process_checker else _ngrok_process_status()
    ngrok_cli = "FOUND" if which("ngrok") else "NOT_FOUND"
    api_status = "NOT_AVAILABLE"
    public_https_url = None
    api_error = ""
    opener = urlopen_func or urllib.request.urlopen
    try:
        with opener(NGROK_API_URL, timeout=timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
        api_status = "AVAILABLE"
        public_https_url = _first_https_tunnel(payload)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        api_error = str(exc)[:180]

    if public_https_url:
        status = "NGROK_HTTPS_TUNNEL_READY"
    elif process_status == "RUNNING" and api_status == "AVAILABLE":
        status = "NGROK_RUNNING_NO_HTTPS_TUNNEL"
    elif process_status == "RUNNING":
        status = "PUBLIC_TUNNEL_NOT_RUNNING"
    elif ngrok_cli == "FOUND":
        status = "NGROK_CLI_FOUND_BUT_TUNNEL_NOT_RUNNING"
    else:
        status = "NGROK_NOT_RUNNING"

    field_capture_public_url = f"{public_https_url.rstrip('/')}/field-capture" if public_https_url else None
    return {
        "ngrok_cli": ngrok_cli,
        "ngrok_process": process_status,
        "ngrok_api": api_status,
        "ngrok_api_url": NGROK_API_URL,
        "public_https_url": public_https_url,
        "field_capture_public_url": field_capture_public_url,
        "checklist_public_url": f"{public_https_url.rstrip('/')}/field-trial-checklist" if public_https_url else None,
        "status": status,
        "operator_command": f"ngrok http {port}",
        "operator_note": "Ngrok probe never opens a tunnel and never reads or writes authtokens.",
        "api_error": api_error,
        "token_policy": "NO_TOKEN_READ_NO_TOKEN_WRITE_NO_AUTHTOKEN_IN_GIT",
    }


def _first_https_tunnel(payload: dict[str, Any]) -> str | None:
    for tunnel in payload.get("tunnels", []):
        public_url = str(tunnel.get("public_url") or "")
        if public_url.startswith("https://"):
            return public_url
    return None


def _ngrok_process_status() -> str:
    if sys.platform.startswith("win"):
        completed = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ngrok.exe"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            return "UNKNOWN"
        return "RUNNING" if "ngrok.exe" in completed.stdout.lower() else "NOT_RUNNING"
    completed = subprocess.run(["pgrep", "-f", "ngrok"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode == 0 and completed.stdout.strip():
        return "RUNNING"
    return "NOT_RUNNING"
