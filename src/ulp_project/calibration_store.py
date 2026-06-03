"""Runtime calibration store helpers. Runtime outputs are ignored by Git."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .calibration_workflow import RUNTIME_CALIBRATION_DIR


def save_calibration_profile(profile: dict[str, Any], runtime_dir: Path = RUNTIME_CALIBRATION_DIR) -> Path:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    calibration_id = str(profile.get("calibration_id") or profile.get("session", {}).get("calibration_id") or "calibration_profile")
    path = runtime_dir / f"{calibration_id}.json"
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_calibration_profile(calibration_id: str, runtime_dir: Path = RUNTIME_CALIBRATION_DIR) -> dict[str, Any]:
    path = runtime_dir / f"{calibration_id}.json"
    if not path.exists():
        return {"status": "CALIBRATION_NOT_READY", "calibration_id": calibration_id}
    return json.loads(path.read_text(encoding="utf-8"))
