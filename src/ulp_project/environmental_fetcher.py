"""Dry-run/fetch helpers for environmental data cache."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .environmental_sources import load_environmental_source_config
from .paths import PROJECT_ROOT

ENV_CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "environmental"


@dataclass(frozen=True)
class EnvironmentalFetchRequest:
    point: str
    latitude: float | None
    longitude: float | None
    observation_date: str
    mode: str = "dry-run"


def build_fetch_request(point: str, lat: float | None, lon: float | None, observation_date: str | None, mode: str) -> EnvironmentalFetchRequest:
    return EnvironmentalFetchRequest(
        point=point,
        latitude=lat,
        longitude=lon,
        observation_date=observation_date or date.today().isoformat(),
        mode=mode,
    )


def fetch_environmental_data(request: EnvironmentalFetchRequest, cache_dir: Path = ENV_CACHE_DIR) -> dict[str, Any]:
    config = load_environmental_source_config()
    if request.mode not in {"dry-run", "fetch"}:
        raise ValueError("mode must be dry-run or fetch")
    payload = {
        "status": "DATA_SOURCE_PARTIAL",
        "request": asdict(request),
        "area": config.get("default_area_name", "Surabaya Utara - Perak"),
        "features": {},
        "missing_sources": ["weather", "soil"],
        "note": "No remote data is fetched in dry-run; fetch mode writes only source-status cache without fake values.",
    }
    if request.mode == "fetch":
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{request.point}_{request.observation_date}.json"
        cache_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        payload["cache_path"] = str(cache_file)
    return payload
