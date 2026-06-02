"""Environmental source registry for Surabaya Utara - Perak."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

DEFAULT_ENV_CONFIG = PROJECT_ROOT / "configs" / "surabaya_perak_environment.yaml"


def load_environmental_source_config(path: Path = DEFAULT_ENV_CONFIG) -> dict[str, Any]:
    if not path.exists():
        return {
            "default_area_name": "Surabaya Utara - Perak",
            "status": "DATA_SOURCE_NOT_CONFIGURED",
            "fallback_policy": {"partial_status": "DATA_SOURCE_PARTIAL", "no_fake_values": True},
        }
    try:
        import yaml
    except ImportError:
        return _minimal_yaml_map(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def environmental_source_status(config: dict[str, Any]) -> dict[str, Any]:
    weather = config.get("weather_sources", {})
    soil = config.get("soil_sources", {})
    configured = [
        name
        for group in (weather, soil)
        for name, item in group.items()
        if isinstance(item, dict) and item.get("status") not in (None, "", "TODO")
    ]
    return {
        "status": "DATA_SOURCE_READY" if configured else "DATA_SOURCE_PARTIAL",
        "configured_sources": configured,
        "missing_sources": [*weather.keys(), *soil.keys()] if not configured else [],
        "area": config.get("default_area_name", "Surabaya Utara - Perak"),
    }


def _minimal_yaml_map(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"') or None
    return result
