"""Registry of environmental data sources; no runtime secrets or mandatory API keys."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "configs" / "environmental_sources.yaml"


def load_environmental_source_registry(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"sources": {}, "status": "ENVIRONMENT_SOURCE_REGISTRY_NOT_FOUND"}
    try:
        import yaml
    except ImportError:
        return {"sources": {}, "status": "YAML_NOT_AVAILABLE"}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {**data, "status": "ENVIRONMENT_SOURCE_REGISTRY_READY"}


def source_availability_summary() -> dict[str, Any]:
    registry = load_environmental_source_registry()
    sources = registry.get("sources", {})
    return {
        "status": registry["status"],
        "manual_csv_ready": "manual_csv_override" in sources,
        "online_sources_configured": [name for name, meta in sources.items() if meta.get("url")],
        "no_api_key_required": True,
    }
