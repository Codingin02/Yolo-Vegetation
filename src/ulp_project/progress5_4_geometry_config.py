"""Progress 5.4 geometry and realtime stability configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

GEOMETRY_CONFIG_PATH = PROJECT_ROOT / "configs" / "electrical_asset_geometry.yaml"
STABILITY_CONFIG_PATH = PROJECT_ROOT / "configs" / "realtime_stability.yaml"

DEFAULT_GEOMETRY_CONFIG = {
    "default_pole_visible_height_m": 10.8,
    "default_pole_total_height_m": 11.0,
    "source_status": "FIELD_DEFAULT_NEEDS_PLN_CONFIRMATION",
    "clearance_critical_m": 3.0,
    "clearance_monitoring_m": 4.0,
    "reference_policy": "CONFIG_OR_CALIBRATION_PROFILE_CAN_OVERRIDE",
}

DEFAULT_STABILITY_CONFIG = {
    "result_update_interval_ms": 1000,
    "max_allowed_latency_ms": 3000,
    "smoothing_window": 5,
    "max_clearance_jump_m_per_update": 0.75,
    "track_hold_ms": 2000,
    "frame_process_fps": 1,
    "overlay_target_fps": 5,
}


def load_geometry_config(path: Path = GEOMETRY_CONFIG_PATH) -> dict[str, Any]:
    return {**DEFAULT_GEOMETRY_CONFIG, **_load_yaml_dict(path)}


def load_stability_config(path: Path = STABILITY_CONFIG_PATH) -> dict[str, Any]:
    return {**DEFAULT_STABILITY_CONFIG, **_load_yaml_dict(path)}


def pole_reference_height_m(config: dict[str, Any] | None = None) -> float:
    cfg = config or load_geometry_config()
    value = cfg.get("default_pole_total_height_m") or cfg.get("default_pole_visible_height_m")
    return float(value or 11.0)


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return _parse_simple_yaml(path)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = _coerce_value(value.strip().strip('"'))
    return result


def _coerce_value(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
