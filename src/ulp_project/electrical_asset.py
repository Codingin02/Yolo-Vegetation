"""Phase 8 electrical asset model for PLN vegetation risk."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ElectricalAssetObservation:
    pole_id: str | None = None
    span_id: str | None = None
    asset_type: str = "other"
    asset_height_m: float | None = None
    asset_lat: float | None = None
    asset_lon: float | None = None
    span_start_pole_id: str | None = None
    span_end_pole_id: str | None = None
    span_mid_sag_height_m: float | None = None
    detected_tree_height_m: float | None = None
    crown_top_m: float | None = None
    horizontal_distance_to_asset_m: float | None = None
    vertical_clearance_m: float | None = None
    minimum_clearance_m: float | None = None
    clearance_source: str = "unknown"
    uncertainty_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_asset_type(asset_type: str | None) -> str:
    value = (asset_type or "other").strip().lower()
    if value in {"conductor", "kabel", "cable"}:
        return "conductor"
    if value in {"span", "bentang"}:
        return "span"
    if value in {"transformer", "trafo"}:
        return "transformer"
    if value in {"pole", "tiang", "struktur_penyangga"}:
        return "pole"
    return "other"
