"""Risk map/GeoJSON exporter under outputs/reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
MAP_HTML = REPORT_DIR / "vegetation_risk_map.html"
GEOJSON = REPORT_DIR / "vegetation_risk_points.geojson"

COLOR_BY_RISK = {
    "AMAN_MONITOR": "green",
    "PERLU_MONITORING": "blue",
    "JADWALKAN_PEMANGKASAN": "orange",
    "PRIORITAS_TINGGI": "red",
    "KRITIS_SEGERA": "darkred",
    "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA": "gray",
}


def row_to_geojson_feature(row: dict[str, Any]) -> dict[str, Any]:
    lat = _to_float(row.get("gps_lat"))
    lon = _to_float(row.get("gps_lon"))
    if lat is None or lon is None:
        return {"status": "GPS_NOT_AVAILABLE", "feature": None}
    return {
        "status": "GPS_READY",
        "feature": {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "point_id": row.get("point_id"),
                "species": row.get("species"),
                "risk_status": row.get("risk_status"),
                "eta_months_mid": row.get("eta_months_mid"),
                "recommended_action": row.get("recommended_action"),
                "nearest_electrical_asset": row.get("nearest_electrical_asset"),
            },
        },
    }


def export_risk_map(rows: list[dict[str, Any]], mode: str = "dry-run", output_dir: Path = REPORT_DIR) -> dict[str, Any]:
    features = []
    gps_missing = 0
    for row in rows:
        feature = row_to_geojson_feature(row)
        if feature["feature"] is None:
            gps_missing += 1
        else:
            features.append(feature["feature"])
    targets = {"html": str(output_dir / "vegetation_risk_map.html"), "geojson": str(output_dir / "vegetation_risk_points.geojson")}
    if mode != "write":
        return {"status": "RISK_MAP_DRY_RUN_READY", "features": len(features), "gps_missing": gps_missing, "targets": targets, "written": False}
    output_dir.mkdir(parents=True, exist_ok=True)
    geojson_payload = {"type": "FeatureCollection", "features": features}
    (output_dir / "vegetation_risk_points.geojson").write_text(json.dumps(geojson_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "vegetation_risk_map.html").write_text(_render_simple_map_html(features), encoding="utf-8")
    return {"status": "RISK_MAP_WRITTEN", "features": len(features), "gps_missing": gps_missing, "targets": targets, "written": True}


def risk_map_status(output_dir: Path = REPORT_DIR) -> dict[str, Any]:
    return {
        "status": "RISK_MAP_READY" if MAP_HTML.exists() and GEOJSON.exists() else "RISK_MAP_NOT_READY",
        "html": str(output_dir / "vegetation_risk_map.html"),
        "geojson": str(output_dir / "vegetation_risk_points.geojson"),
    }


def _render_simple_map_html(features: list[dict[str, Any]]) -> str:
    rows = []
    for feature in features:
        props = feature["properties"]
        rows.append(
            f"<li>{props.get('point_id')} - {props.get('risk_status')} - {props.get('recommended_action')}</li>"
        )
    return "<html><body><h1>Vegetation Risk Map Export</h1><ul>" + "".join(rows) + "</ul></body></html>"


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
