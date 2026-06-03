"""Map report policy: no GPS, no marker."""

from __future__ import annotations

from typing import Any


def should_create_map_marker(row: dict[str, Any]) -> dict[str, Any]:
    lat = _float(row.get("latitude") or row.get("gps_lat"))
    lon = _float(row.get("longitude") or row.get("gps_lon"))
    if lat is None or lon is None:
        return {"status": "NO_GPS_NO_MAP_MARKER", "write_marker": False}
    return {"status": "MAP_MARKER_ALLOWED", "write_marker": True, "latitude": lat, "longitude": lon, "color": marker_color(row.get("risk_priority"))}


def marker_color(risk_priority: str | None) -> str:
    return {
        "CRITICAL": "red",
        "HIGH": "orange",
        "MEDIUM": "yellow",
        "LOW": "green",
        "SAFE": "green",
        "INSUFFICIENT_DATA": "gray",
    }.get(str(risk_priority or "INSUFFICIENT_DATA"), "gray")


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
