"""Species growth profile loader for Phase 8 ETA."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

DEFAULT_PROFILE_PATH = PROJECT_ROOT / "configs" / "species_growth_profiles.yaml"


def load_species_profiles(path: Path = DEFAULT_PROFILE_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"species": {}}
    try:
        import yaml
    except ImportError:
        return {"species": {}}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"species": {}}


def get_species_profile(species_name: str, profiles: dict[str, Any] | None = None) -> dict[str, Any]:
    profiles = profiles or load_species_profiles()
    species = profiles.get("species", {})
    return species.get(species_name) or species.get("generic_tree") or {}
