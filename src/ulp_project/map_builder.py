"""Map builder contract with dry-run default."""

from __future__ import annotations

from pathlib import Path

from .gps_linker import collect_gps_link_status
from .gps_map import build_map, read_field_points
from .paths import GPS_FIELD_POINTS_DIR, RESULTS_MAP_DIR


def build_field_map_status(
    gps_dir: Path = GPS_FIELD_POINTS_DIR,
    output: Path = RESULTS_MAP_DIR / "field_points_map.html",
    mode: str = "dry-run",
) -> dict[str, object]:
    if mode not in {"dry-run", "write"}:
        raise ValueError("mode must be dry-run or write")
    gps_status = collect_gps_link_status(gps_dir)
    if mode == "dry-run":
        return {
            "status": gps_status["status"],
            "mode": "dry-run",
            "points_found": gps_status["point_count"],
            "output": str(output),
            "written": False,
        }
    points = read_field_points(gps_dir)
    status = build_map(points, output)
    return {
        "status": status,
        "mode": "write",
        "points_found": len(points),
        "output": str(output),
        "written": status == "READY",
    }
