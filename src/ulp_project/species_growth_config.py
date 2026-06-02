"""Species growth configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

DEFAULT_SPECIES_CONFIG = PROJECT_ROOT / "configs" / "tree_species_growth.yaml"


def load_species_growth_config(path: Path = DEFAULT_SPECIES_CONFIG) -> dict[str, Any]:
    if not path.exists():
        return {"species": {}}
    try:
        import yaml
    except ImportError:
        return {"species": {}}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"species": {}}


def get_species_config(species: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_species_growth_config()
    species_map = config.get("species", {})
    return species_map.get(species) or species_map.get("unknown_tree") or {}
