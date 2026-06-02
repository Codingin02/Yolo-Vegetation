"""Field point registry parsing with P/K/V naming preserved."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from pathlib import Path


POINT_NAME_PATTERN = re.compile(r"^[PKV]\d{3}_[A-Za-z0-9_]+$")


@dataclass(frozen=True)
class FieldPointRecord:
    point_id: str
    object_type: str
    point_name: str
    latitude: float | None
    longitude: float | None
    risk_level: str
    status: str
    notes: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_point_name(point_name: str) -> bool:
    return bool(POINT_NAME_PATTERN.match(point_name or ""))


def load_field_point_registry(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "POINT_REGISTRY_NOT_READY", "points": [], "invalid_points": []}
    points: list[FieldPointRecord] = []
    invalid: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            point_name = row.get("point_name", "")
            if not validate_point_name(point_name):
                invalid.append(point_name)
            lat = _to_float(row.get("latitude"))
            lon = _to_float(row.get("longitude"))
            points.append(
                FieldPointRecord(
                    point_id=row.get("point_id", ""),
                    object_type=row.get("object_type", ""),
                    point_name=point_name,
                    latitude=lat,
                    longitude=lon,
                    risk_level=row.get("risk_level", "UNKNOWN") or "UNKNOWN",
                    status=row.get("status", "UNKNOWN") or "UNKNOWN",
                    notes=row.get("notes", ""),
                )
            )
    return {
        "status": "READY" if points and not invalid else "POINT_REGISTRY_PARTIAL",
        "points": [point.to_dict() for point in points],
        "invalid_points": invalid,
    }


def _to_float(value: str | None) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except ValueError:
        return None
