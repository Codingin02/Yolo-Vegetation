"""Manual tunnel diagnostics without storing tokens."""

from __future__ import annotations

import shutil


def tunnel_cli_status() -> dict[str, object]:
    return {
        "ngrok": "AVAILABLE" if shutil.which("ngrok") else "NOT_FOUND",
        "cloudflared": "AVAILABLE" if shutil.which("cloudflared") else "NOT_FOUND",
        "commands": ["ngrok http 5000", "cloudflared tunnel --url http://localhost:5000"],
        "token_policy": "env_or_cli_only_do_not_commit",
    }
