"""Simple origin guard for remote prototype."""

from __future__ import annotations

from typing import Any


def check_origin(origin: str | None, allowed_origins: list[str] | None = None, security_enabled: bool = True) -> dict[str, Any]:
    if not security_enabled:
        return {"status": "ORIGIN_GUARD_DISABLED", "allowed": True}
    if not origin:
        return {"status": "ORIGIN_NOT_PROVIDED_ALLOW_LOCAL_TEST", "allowed": True}
    allowed_origins = allowed_origins or []
    if origin in allowed_origins or origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
        return {"status": "ORIGIN_ALLOWED", "allowed": True}
    return {"status": "ORIGIN_REVIEW_REQUIRED", "allowed": False}
