"""Combined runtime diagnostics for remote field trial."""

from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from .calibration_workflow import validate_calibration_payload
from .environmental_manual_loader import validate_environmental_manual_csv
from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT
from .realtime_streaming import websocket_available
from .tunnel_diagnostics import tunnel_cli_status
from .windows_firewall_hint import windows_firewall_hint


def collect_remote_field_trial_diagnostics(port: int = 5000) -> dict[str, Any]:
    return {
        "status": "REMOTE_FIELD_TRIAL_DIAGNOSTICS_READY",
        "python_executable": sys.executable,
        "venv_active": "venv" in sys.executable.lower(),
        "flask_import": _import_status("flask"),
        "flask_sock_import": _import_status("flask_sock"),
        "project_root": str(PROJECT_ROOT),
        "git_branch": _git(["branch", "--show-current"]),
        "git_commit": _git(["rev-parse", "--short", "HEAD"]),
        "model": check_model_handoff(),
        "calibration": validate_calibration_payload({}),
        "environmental": validate_environmental_manual_csv(),
        "port_available": _port_available(port),
        "websocket": websocket_available(),
        "outputs_writable": _writable(PROJECT_ROOT / "outputs" / "reports"),
        "runtime_writable": _writable(PROJECT_ROOT / "data" / "runtime"),
        "local_url": f"http://127.0.0.1:{port}/field-capture",
        "tunnel": tunnel_cli_status(),
        "firewall": windows_firewall_hint(port),
        "no_label_touch": True,
    }


def _import_status(module: str) -> str:
    try:
        __import__(module)
        return "OK"
    except ImportError:
        return f"{module.upper()}_NOT_INSTALLED"


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=PROJECT_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else completed.stderr.strip()


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _writable(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".diagnostic_probe.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return {"path": str(path), "status": "WRITABLE"}
    except OSError as exc:
        return {"path": str(path), "status": "NOT_WRITABLE", "error": str(exc)}
