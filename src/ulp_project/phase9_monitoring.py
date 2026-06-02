"""Phase 9 CSV monitoring and map outputs for rough realtime demo."""

from __future__ import annotations

import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
MONITORING_CSV = REPORT_DIR / "vegetation_risk_monitoring.csv"
RISK_MAP_HTML = REPORT_DIR / "vegetation_risk_map.html"
SPOOL_DIR = REPORT_DIR / "spool"

PHASE9_MONITORING_COLUMNS = [
    "inspection_id",
    "timestamp",
    "job_id",
    "point_id",
    "species",
    "asset_type",
    "latitude",
    "longitude",
    "tree_height_m",
    "asset_height_m",
    "span_lowest_point_height_m",
    "cable_height_m",
    "cable_or_span_height_m",
    "clearance_m",
    "growth_rate_m_per_day",
    "adjusted_growth_rate_m_per_day",
    "eta_days",
    "eta_months",
    "risk_priority",
    "action_recommendation",
    "status",
    "mode",
    "reason",
    "season",
    "rainfall_mm",
    "temperature_c",
    "relative_humidity_percent",
    "soil_moisture",
    "soil_ph",
    "solar_radiation",
    "evapotranspiration",
    "wind_speed",
    "environmental_source",
    "measurement_source",
    "confidence_status",
    "image_path",
    "photo_path",
    "map_link",
    "environment_source_status",
    "environmental_data_status",
    "calibration_status",
    "model_status",
    "operator_notes",
]


def build_phase9_monitoring_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "inspection_id": payload.get("inspection_id", ""),
        "timestamp": payload.get("timestamp") or datetime.now().isoformat(),
        "job_id": payload.get("job_id", ""),
        "point_id": payload.get("point_id", ""),
        "species": payload.get("species", "pohon_sono"),
        "asset_type": payload.get("asset_type", "span"),
        "latitude": payload.get("latitude", ""),
        "longitude": payload.get("longitude", ""),
        "tree_height_m": payload.get("tree_height_m", ""),
        "asset_height_m": payload.get("asset_height_m", ""),
        "span_lowest_point_height_m": payload.get("span_lowest_point_height_m", ""),
        "cable_height_m": payload.get("cable_height_m", ""),
        "cable_or_span_height_m": payload.get("cable_or_span_height_m", ""),
        "clearance_m": payload.get("clearance_m", ""),
        "growth_rate_m_per_day": payload.get("growth_rate_m_per_day", ""),
        "adjusted_growth_rate_m_per_day": payload.get("adjusted_growth_rate_m_per_day", ""),
        "eta_days": payload.get("eta_days", ""),
        "eta_months": payload.get("eta_months", ""),
        "risk_priority": payload.get("risk_priority", ""),
        "action_recommendation": payload.get("action_recommendation", ""),
        "status": payload.get("status", ""),
        "mode": payload.get("mode", ""),
        "reason": payload.get("reason") or payload.get("status_reason", ""),
        "season": payload.get("season", ""),
        "rainfall_mm": payload.get("rainfall_mm", ""),
        "temperature_c": payload.get("temperature_c", ""),
        "relative_humidity_percent": payload.get("relative_humidity_percent", ""),
        "soil_moisture": payload.get("soil_moisture", ""),
        "soil_ph": payload.get("soil_ph", ""),
        "solar_radiation": payload.get("solar_radiation", ""),
        "evapotranspiration": payload.get("evapotranspiration", ""),
        "wind_speed": payload.get("wind_speed", ""),
        "environmental_source": payload.get("environmental_source", ""),
        "measurement_source": payload.get("measurement_source", "manual"),
        "confidence_status": payload.get("confidence_status", "PROVISIONAL"),
        "image_path": payload.get("image_path") or payload.get("photo_path", ""),
        "photo_path": payload.get("photo_path") or payload.get("image_path", ""),
        "map_link": payload.get("map_link", ""),
        "environment_source_status": payload.get("environment_source_status") or payload.get("environmental_data_status", "ENVIRONMENT_NOT_REQUIRED_FOR_MANUAL_DEMO"),
        "environmental_data_status": payload.get("environmental_data_status") or payload.get("environment_source_status", "ENVIRONMENT_NOT_REQUIRED_FOR_MANUAL_DEMO"),
        "calibration_status": payload.get("calibration_status", "MANUAL_CLEARANCE_PROVISIONAL"),
        "model_status": payload.get("model_status", "MODEL_NOT_READY"),
        "operator_notes": payload.get("operator_notes") or payload.get("notes", ""),
    }


def append_monitoring_row(row: dict[str, Any], output: Path = MONITORING_CSV, retries: int = 3, retry_delay_sec: float = 0.15) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            _append_row_to_csv(row, output)
            return {
                "status": "REPORT_WRITTEN_MAIN_CSV",
                "path": str(output),
                "written": True,
                "attempts": attempt,
                "operator_warning": "",
            }
        except PermissionError as exc:
            last_error = str(exc)
            time.sleep(retry_delay_sec)
    try:
        spool_path = _spool_path()
        _append_row_to_csv(row, spool_path)
        return {
            "status": "REPORT_WRITTEN_SPOOL_CSV_LOCKED",
            "path": str(spool_path),
            "main_csv_path": str(output),
            "written": True,
            "attempts": retries,
            "operator_warning": "CSV sedang terkunci. Tutup Excel atau gunakan fallback spool.",
            "error": last_error,
        }
    except OSError as exc:
        return {
            "status": "REPORT_WRITE_FAILED",
            "path": str(output),
            "written": False,
            "attempts": retries,
            "operator_warning": "CSV tidak bisa ditulis. Cek permission folder outputs/reports.",
            "error": str(exc),
        }


def _append_row_to_csv(row: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    exists = output.exists()
    with output.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PHASE9_MONITORING_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow({column: row.get(column, "") for column in PHASE9_MONITORING_COLUMNS})


def _spool_path() -> Path:
    SPOOL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return SPOOL_DIR / f"vegetation_risk_monitoring_{stamp}.csv"


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
        f"action: {row.get('action_recommendation')}<br>"
        f"confidence: {row.get('confidence_status')}<br>"
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
