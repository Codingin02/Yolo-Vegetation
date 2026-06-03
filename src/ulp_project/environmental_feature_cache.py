"""Runtime environmental cache helpers; cache directory is ignored by Git."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

CACHE_DIR = PROJECT_ROOT / "data" / "runtime" / "environmental"


def write_environmental_cache(key: str, payload: dict[str, Any], cache_dir: Path = CACHE_DIR) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{key}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_environmental_cache(key: str, cache_dir: Path = CACHE_DIR) -> dict[str, Any]:
    path = cache_dir / f"{key}.json"
    if not path.exists():
        return {"status": "ENVIRONMENT_CACHE_NOT_FOUND"}
    return json.loads(path.read_text(encoding="utf-8"))
