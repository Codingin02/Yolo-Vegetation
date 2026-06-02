"""Runtime error logging for API hardening."""

from __future__ import annotations

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

LOG_DIR = PROJECT_ROOT / "data" / "runtime" / "logs"
LATEST_ERROR_JSON = LOG_DIR / "latest_api_error.json"


def write_api_error(error: BaseException, request_path: str) -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "request_path": request_path,
        "error_type": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exc(),
    }
    LATEST_ERROR_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def latest_api_error() -> dict[str, Any]:
    if not LATEST_ERROR_JSON.exists():
        return {"status": "NO_API_ERROR_LOGGED", "path": str(LATEST_ERROR_JSON)}
    return {"status": "LATEST_API_ERROR_READY", **json.loads(LATEST_ERROR_JSON.read_text(encoding="utf-8"))}
