"""Structured field inspection input for provisional ETA processing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4


def parse_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_text(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value)


@dataclass(slots=True)
class FieldInspectionRecord:
    inspection_id: str
    timestamp: str
    point_id: str
    species: str
    asset_type: str
    latitude: float | None = None
    longitude: float | None = None
    tree_height_m: float | None = None
    asset_height_m: float | None = None
    span_lowest_point_height_m: float | None = None
    cable_height_m: float | None = None
    transformer_clearance_m: float | None = None
    clearance_m: float | None = None
    growth_rate_m_per_day: float | None = None
    season: str = ""
    rainfall_mm: float | None = None
    temperature_c: float | None = None
    relative_humidity_percent: float | None = None
    soil_moisture: float | None = None
    soil_ph: float | None = None
    solar_radiation: float | None = None
    evapotranspiration: float | None = None
    wind_speed: float | None = None
    environmental_source: str = ""
    measurement_source: str = "manual"
    confidence_status: str = "PROVISIONAL"
    notes: str = ""
    photo_path: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any], photo_path: str = "") -> "FieldInspectionRecord":
        timestamp = parse_text(payload.get("timestamp"), datetime.now().isoformat())
        inspection_id = parse_text(payload.get("inspection_id") or payload.get("job_id"), f"inspection_{uuid4().hex[:12]}")
        latitude = parse_float(payload.get("latitude") or payload.get("lat"))
        longitude = parse_float(payload.get("longitude") or payload.get("lon"))
        asset_height = parse_float(payload.get("asset_height_m") or payload.get("cable_or_span_height_m"))
        return cls(
            inspection_id=inspection_id,
            timestamp=timestamp,
            point_id=parse_text(payload.get("point_id"), "V001_pohon_sono"),
            species=parse_text(payload.get("species") or payload.get("manual_object_type"), "pohon_sono"),
            asset_type=parse_text(payload.get("asset_type"), "span"),
            latitude=latitude,
            longitude=longitude,
            tree_height_m=parse_float(payload.get("tree_height_m")),
            asset_height_m=asset_height,
            span_lowest_point_height_m=parse_float(payload.get("span_lowest_point_height_m")),
            cable_height_m=parse_float(payload.get("cable_height_m")),
            transformer_clearance_m=parse_float(payload.get("transformer_clearance_m")),
            clearance_m=parse_float(payload.get("clearance_m")),
            growth_rate_m_per_day=parse_float(payload.get("growth_rate_m_per_day")),
            season=parse_text(payload.get("season")),
            rainfall_mm=parse_float(payload.get("rainfall_mm")),
            temperature_c=parse_float(payload.get("temperature_c")),
            relative_humidity_percent=parse_float(payload.get("relative_humidity_percent")),
            soil_moisture=parse_float(payload.get("soil_moisture")),
            soil_ph=parse_float(payload.get("soil_ph")),
            solar_radiation=parse_float(payload.get("solar_radiation")),
            evapotranspiration=parse_float(payload.get("evapotranspiration")),
            wind_speed=parse_float(payload.get("wind_speed")),
            environmental_source=parse_text(payload.get("environmental_source"), "manual_or_not_provided"),
            measurement_source=parse_text(payload.get("measurement_source"), "manual"),
            confidence_status=parse_text(payload.get("confidence_status"), "PROVISIONAL"),
            notes=parse_text(payload.get("notes") or payload.get("operator_note")),
            photo_path=photo_path,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
