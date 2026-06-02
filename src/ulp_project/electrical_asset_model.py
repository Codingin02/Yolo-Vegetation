"""Electrical asset and vegetation observation data contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ElectricalAsset:
    asset_type: str
    asset_id: str
    point_id: str
    gps_lat: float | None = None
    gps_lon: float | None = None
    bbox: list[float] | None = None
    estimated_height_m: float | None = None
    estimated_clearance_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VegetationObservation:
    point_id: str
    species: str
    observation_time: str
    gps_lat: float | None = None
    gps_lon: float | None = None
    detected_height_m: float | None = None
    canopy_bbox: list[float] | None = None
    trunk_bbox: list[float] | None = None
    nearest_asset_type: str | None = None
    nearest_asset_clearance_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
