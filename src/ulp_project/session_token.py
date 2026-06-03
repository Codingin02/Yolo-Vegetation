"""Runtime-only session token helpers."""

from __future__ import annotations

import secrets
from pathlib import Path

from .paths import PROJECT_ROOT

TOKEN_DIR = PROJECT_ROOT / "data" / "runtime" / "tokens"


def generate_session_token(session_id: str, token_dir: Path = TOKEN_DIR) -> dict[str, str]:
    token_dir.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(24)
    (token_dir / f"{session_id}.token").write_text(token, encoding="utf-8")
    return {"status": "SESSION_TOKEN_GENERATED_RUNTIME_ONLY", "session_id": session_id, "token": token}


def token_git_policy() -> dict[str, object]:
    return {"token_dir": str(TOKEN_DIR), "git_ignored": True, "do_not_commit": True}
