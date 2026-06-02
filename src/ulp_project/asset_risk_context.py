"""Electrical asset context for provisional field risk calculation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class AssetRiskContext:
    asset_type: str
    pole_id: str = ""
    span_id: str = ""
    asset_height_m: float | None = None
    span_lowest_point_height_m: float | None = None
    cable_height_m: float | None = None
    transformer_clearance_m: float | None = None
    clearance_m: float | None = None
    clearance_source: str = "manual_or_unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
