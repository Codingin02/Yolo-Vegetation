"""Non-invasive diagnostics for Progress 5.3 field-trial execution."""

from __future__ import annotations

import socket
import subprocess
import urllib.error
import urllib.request
from typing import Any

from .paths import PROJECT_ROOT
from .runtime_links import build_public_links, detect_lan_ips


def collect_field_trial_diagnostics(port: int = 5000, *, timeout_s: float = 1.0) -> dict[str, Any]:
    port_status = diagnose_port(port)
    return {
        "status": "FIELD_TRIAL_DIAGNOSTICS_READY",
        "project_root": str(PROJECT_ROOT),
        "local_health": probe_local_health(port=port, timeout_s=timeout_s),
        "port": port_status,
        "lan_candidate_ips": detect_lan_ips(),
        "public_links": build_public_links(port=port),
        "windows_firewall": {
            "status": "UNKNOWN_MANUAL_CHECK_REQUIRED",
            "note": "Script tidak mengubah firewall. Izinkan Python pada Private Network secara manual bila LAN HTTP diblokir.",
            "manual_path": "Windows Security > Firewall & network protection > Allow an app through firewall > Python > Private",
        },
        "server_start_stop_safety": {
            "status": "NO_BACKGROUND_SERVICE_NO_AUTORUN",
            "note": "Field trial memakai Flask dev/runtime command manual, bukan production service permanen.",
        },
    }


def diagnose_port(port: int = 5000) -> dict[str, Any]:
    listening = _is_port_listening(port)
    process_hint = _port_process_hint(port)
    return {
        "port": port,
        "listening": listening,
        "status": f"PORT_{port}_LISTENING" if listening else f"PORT_{port}_NOT_LISTENING",
        "process_hint": process_hint,
        "operator_note": "Jika port bentrok, hentikan proses lama atau jalankan server pada port lain.",
    }


def probe_local_health(port: int = 5000, *, timeout_s: float = 1.0) -> dict[str, Any]:
    url = f"http://127.0.0.1:{port}/api/network/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:
            status_code = getattr(response, "status", 200)
            return {"status": "LOCAL_SERVER_HEALTH_OK", "url": url, "status_code": status_code}
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        return {
            "status": "LOCAL_SERVER_HEALTH_NOT_REACHABLE",
            "url": url,
            "error": str(exc)[:180],
            "next_action": f".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port {port}",
        }


def _is_port_listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _port_process_hint(port: int) -> dict[str, str]:
    completed = subprocess.run(["netstat", "-ano", "-p", "tcp"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        return {"status": "UNKNOWN", "error": completed.stderr[:180]}
    matches = [line.strip() for line in completed.stdout.splitlines() if f":{port} " in line and "LISTENING" in line.upper()]
    if not matches:
        return {"status": "NO_LISTENING_PROCESS_FOUND"}
    return {"status": "LISTENING_PROCESS_FOUND", "netstat": matches[0][:220]}
