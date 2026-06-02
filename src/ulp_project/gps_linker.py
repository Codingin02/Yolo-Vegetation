"""GPS linker contract that reads optional GPS files without writing outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .gps_map import FieldPoint, read_field_points
from .paths import GPS_FIELD_POINTS_DIR


@dataclass(frozen=True)
class GPSLinkStatus:
    status: str
    gps_dir: str
    point_count: int
    points: list[dict[str, object]]


def collect_gps_link_status(gps_dir: Path = GPS_FIELD_POINTS_DIR) -> dict[str, object]:
    points: list[FieldPoint] = read_field_points(gps_dir)
    status = GPSLinkStatus(
        status="READY" if points else "GPS_DATA_NOT_READY",
        gps_dir=str(gps_dir),
        point_count=len(points),
        points=[
            {
                "name": point.name,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "source": str(point.source),
            }
            for point in points
        ],
    )
    return asdict(status)
