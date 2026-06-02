"""Map runtime for field registry CSV, writing only under outputs/maps."""

from __future__ import annotations

import json
from pathlib import Path

from .paths import PROJECT_ROOT
from .point_registry import load_field_point_registry

OUTPUT_MAP_DIR = PROJECT_ROOT / "outputs" / "maps"

RISK_COLORS = {
    "LOW": "green",
    "MEDIUM": "orange",
    "HIGH": "red",
    "CRITICAL": "darkred",
    "WAITING_MODEL": "gray",
    "UNKNOWN": "gray",
}


def build_system_map(
    registry_csv: Path,
    output: Path = OUTPUT_MAP_DIR / "field_system_map.html",
    risk_path: Path | None = None,
    mode: str = "dry-run",
) -> dict[str, object]:
    if mode not in {"dry-run", "write"}:
        raise ValueError("mode must be dry-run or write")
    registry = load_field_point_registry(registry_csv)
    points = registry["points"]
    gps_ready = [point for point in points if point.get("latitude") is not None and point.get("longitude") is not None]
    status = "READY" if gps_ready else "GPS_DATA_NOT_READY"
    if mode == "dry-run":
        return {"status": status, "mode": mode, "points": len(points), "gps_ready": len(gps_ready), "output": str(output), "written": False}
    if not str(output.resolve()).startswith(str(OUTPUT_MAP_DIR.resolve())):
        return {"status": "OUTPUT_PATH_NOT_ALLOWED", "mode": mode, "output": str(output), "written": False}
    if not gps_ready:
        return {"status": "GPS_DATA_NOT_READY", "mode": mode, "points": len(points), "gps_ready": 0, "output": str(output), "written": False}
    try:
        import folium
    except ImportError:
        return {"status": "DEPENDENCY_MISSING_FOLIUM", "mode": mode, "output": str(output), "written": False}
    risk_by_point = _load_risk_lookup(risk_path)
    center = [
        sum(float(point["latitude"]) for point in gps_ready) / len(gps_ready),
        sum(float(point["longitude"]) for point in gps_ready) / len(gps_ready),
    ]
    fmap = folium.Map(location=center, zoom_start=16, tiles="CartoDB Positron")
    for point in gps_ready:
        risk_payload = risk_by_point.get(point["point_name"]) or risk_by_point.get(point["point_id"]) or {}
        risk_level = str(risk_payload.get("risk_level") or risk_payload.get("electrical_clearance_risk_level") or point.get("risk_level") or "UNKNOWN")
        marker_status = "WAITING_MODEL" if risk_level in {"", "UNKNOWN"} else risk_level
        popup = (
            f"point_id: {point['point_id']}<br>"
            f"object_type: {point['object_type']}<br>"
            f"risk_level: {risk_level}<br>"
            f"status: {point['status']}<br>"
            f"job_id: {risk_payload.get('job_id', '')}<br>"
            f"model_status: {risk_payload.get('model_status', 'MODEL_NOT_READY')}<br>"
            f"notes: {point['notes']}"
        )
        folium.Marker(
            [point["latitude"], point["longitude"]],
            popup=popup,
            tooltip=point["point_name"],
            icon=folium.Icon(color=RISK_COLORS.get(marker_status, "gray")),
        ).add_to(fmap)
    output.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output))
    return {"status": "READY", "mode": mode, "points": len(points), "gps_ready": len(gps_ready), "output": str(output), "written": True}


def _load_risk_lookup(risk_path: Path | None) -> dict[str, dict[str, object]]:
    if not risk_path or not risk_path.exists():
        return {}
    if risk_path.suffix.lower() == ".json":
        payload = json.loads(risk_path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return {str(item.get("point_name") or item.get("point_id")): item for item in payload if isinstance(item, dict)}
        if isinstance(payload, dict):
            items = payload.get("results") if isinstance(payload.get("results"), list) else [payload]
            return {str(item.get("point_name") or item.get("point_id")): item for item in items if isinstance(item, dict)}
    return {}
