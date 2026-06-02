"""Phase 9 CSV monitoring and map outputs for rough realtime demo."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
MONITORING_CSV = REPORT_DIR / "vegetation_risk_monitoring.csv"
RISK_MAP_HTML = REPORT_DIR / "vegetation_risk_map.html"

PHASE9_MONITORING_COLUMNS = [
    "timestamp",
    "job_id",
    "point_id",
    "species",
    "asset_type",
    "latitude",
    "longitude",
    "tree_height_m",
    "cable_or_span_height_m",
    "clearance_m",
    "growth_rate_m_per_day",
    "eta_days",
    "eta_months",
    "risk_priority",
    "status",
    "mode",
    "reason",
    "image_path",
    "environment_source_status",
    "calibration_status",
    "model_status",
    "operator_notes",
]


def build_phase9_monitoring_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": payload.get("timestamp") or datetime.now().isoformat(),
        "job_id": payload.get("job_id", ""),
        "point_id": payload.get("point_id", ""),
        "species": payload.get("species", "pohon_sono"),
        "asset_type": payload.get("asset_type", "span"),
        "latitude": payload.get("latitude", ""),
        "longitude": payload.get("longitude", ""),
        "tree_height_m": payload.get("tree_height_m", ""),
        "cable_or_span_height_m": payload.get("cable_or_span_height_m", ""),
        "clearance_m": payload.get("clearance_m", ""),
        "growth_rate_m_per_day": payload.get("growth_rate_m_per_day", ""),
        "eta_days": payload.get("eta_days", ""),
        "eta_months": payload.get("eta_months", ""),
        "risk_priority": payload.get("risk_priority", ""),
        "status": payload.get("status", ""),
        "mode": payload.get("mode", ""),
        "reason": payload.get("reason", ""),
        "image_path": payload.get("image_path", ""),
        "environment_source_status": payload.get("environment_source_status", "ENVIRONMENT_NOT_REQUIRED_FOR_MANUAL_DEMO"),
        "calibration_status": payload.get("calibration_status", "MANUAL_CLEARANCE_PROVISIONAL"),
        "model_status": payload.get("model_status", "MODEL_NOT_READY"),
        "operator_notes": payload.get("operator_notes", ""),
    }


def append_monitoring_row(row: dict[str, Any], output: Path = MONITORING_CSV) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    exists = output.exists()
    with output.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PHASE9_MONITORING_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow({column: row.get(column, "") for column in PHASE9_MONITORING_COLUMNS})
    return {"status": "CSV_REPORT_WRITTEN", "path": str(output), "written": True}


def write_phase9_risk_map(row: dict[str, Any], output: Path = RISK_MAP_HTML) -> dict[str, Any]:
    lat = _to_float(row.get("latitude"))
    lon = _to_float(row.get("longitude"))
    if lat is None or lon is None:
        return {"status": "NO_GPS_NO_MAP_MARKER", "path": str(output), "written": False, "reason": "NO_GPS_NO_MAP_MARKER"}
    output.parent.mkdir(parents=True, exist_ok=True)
    popup = (
        f"point_id: {row.get('point_id')}<br>"
        f"species: {row.get('species')}<br>"
        f"asset_type: {row.get('asset_type')}<br>"
        f"clearance_m: {row.get('clearance_m')}<br>"
        f"eta_days: {row.get('eta_days')}<br>"
        f"eta_months: {row.get('eta_months')}<br>"
        f"risk_priority: {row.get('risk_priority')}<br>"
        f"status: {row.get('status')}<br>"
        f"notes: {row.get('operator_notes')}"
    )
    html = (
        "<html><body><h1>Vegetation Risk Map</h1>"
        f"<p>Marker: {lat}, {lon}</p><div>{popup}</div>"
        "</body></html>"
    )
    output.write_text(html, encoding="utf-8")
    return {"status": "MAP_MARKER_WRITTEN", "path": str(output), "written": True, "reason": "GPS_AVAILABLE"}


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
