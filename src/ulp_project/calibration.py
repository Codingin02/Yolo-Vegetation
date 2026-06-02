"""Calibration config helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

DEFAULT_CALIBRATION_CONFIG = PROJECT_ROOT / "configs" / "calibration_schema.yaml"


def _parse_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped == "":
        return None
    try:
        return float(stripped)
    except ValueError:
        return stripped


def load_calibration_config(path: Path = DEFAULT_CALIBRATION_CONFIG) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "CALIBRATION_NOT_READY",
            "clearance_thresholds_m": {"danger_below": 1.5, "warning_below": 3.0, "safe_at_or_above": 3.0},
        }
    try:
        import yaml
    except ImportError:
        # Minimal fallback for this simple schema.
        config: dict[str, Any] = {"clearance_thresholds_m": {}}
        section = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("-"):
                continue
            if not line.startswith(" ") and line.endswith(":"):
                section = line.strip()[:-1]
                config.setdefault(section, {})
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = _parse_scalar(value)
                if line.startswith(" ") and section:
                    config.setdefault(section, {})[key] = value
                else:
                    config[key] = value
        return config
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded


def estimate_pixel_scale(
    known_object_width_m: float | None = None,
    known_object_width_px: float | None = None,
    meters_per_pixel: float | None = None,
) -> dict[str, Any]:
    if meters_per_pixel and meters_per_pixel > 0:
        return {"status": "READY", "meters_per_pixel": float(meters_per_pixel)}
    if not known_object_width_m or not known_object_width_px or known_object_width_px <= 0:
        return {"status": "CALIBRATION_NOT_READY", "meters_per_pixel": None}
    return {"status": "READY", "meters_per_pixel": float(known_object_width_m) / float(known_object_width_px)}
