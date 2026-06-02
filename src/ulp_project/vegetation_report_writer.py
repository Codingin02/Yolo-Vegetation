"""Vegetation risk report writer for CSV/JSON outputs."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .risk_decision_engine import ACTION_BY_STATUS, PRIORITY_BY_STATUS
from .sheets_report_schema import REPORT_COLUMNS, empty_report_row, validate_report_row

REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
CSV_REPORT = REPORT_DIR / "vegetation_risk_report.csv"
LATEST_JSON = REPORT_DIR / "latest_vegetation_risk_report.json"


def build_report_row(payload: dict[str, Any]) -> dict[str, Any]:
    row = empty_report_row()
    risk_status = payload.get("risk_status") or "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA"
    row.update(
        {
            "report_id": payload.get("report_id") or f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp_wib": payload.get("timestamp_wib") or datetime.now().isoformat(),
            "point_id": payload.get("point_id", ""),
            "gps_lat": payload.get("gps_lat", ""),
            "gps_lon": payload.get("gps_lon", ""),
            "address_or_area": payload.get("address_or_area", "Surabaya Utara - Perak"),
            "species": payload.get("species", "pohon_sono"),
            "detected_object": payload.get("detected_object", "MODEL_NOT_READY"),
            "nearest_electrical_asset": payload.get("nearest_electrical_asset", "unknown"),
            "span_id": payload.get("span_id", ""),
            "pole_pair_id": payload.get("pole_pair_id", ""),
            "tree_height_m": payload.get("tree_height_m", ""),
            "tree_height_confidence": payload.get("tree_height_confidence", "LOW"),
            "clearance_to_asset_m": payload.get("clearance_to_asset_m", ""),
            "clearance_confidence": payload.get("clearance_confidence", "LOW"),
            "season_label": payload.get("season_label", "unknown"),
            "rainfall_mm_7d": payload.get("rainfall_mm_7d", ""),
            "rainfall_mm_30d": payload.get("rainfall_mm_30d", ""),
            "temperature_c_mean_30d": payload.get("temperature_c_mean_30d", ""),
            "humidity_mean_30d": payload.get("humidity_mean_30d", ""),
            "soil_ph": payload.get("soil_ph", ""),
            "soil_moisture_proxy": payload.get("soil_moisture_proxy", ""),
            "growth_rate_m_per_day_min": payload.get("growth_rate_m_per_day_min", ""),
            "growth_rate_m_per_day_mid": payload.get("growth_rate_m_per_day_mid", ""),
            "growth_rate_m_per_day_max": payload.get("growth_rate_m_per_day_max", ""),
            "eta_days_min": payload.get("eta_days_min", ""),
            "eta_days_mid": payload.get("eta_days_mid", ""),
            "eta_days_max": payload.get("eta_days_max", ""),
            "eta_months_mid": payload.get("eta_months_mid", ""),
            "risk_status": risk_status,
            "recommended_action": payload.get("recommended_action") or ACTION_BY_STATUS.get(risk_status, "Lengkapi data kalibrasi/lingkungan"),
            "priority_rank": payload.get("priority_rank") or PRIORITY_BY_STATUS.get(risk_status, 99),
            "model_status": payload.get("model_status", "MODEL_NOT_READY"),
            "calibration_status": payload.get("calibration_status", "CALIBRATION_NOT_READY"),
            "environmental_data_status": payload.get("environmental_data_status", "ENVIRONMENTAL_DATA_NOT_READY"),
            "data_quality_flags": payload.get("data_quality_flags", "MODEL_NOT_READY;CALIBRATION_NOT_READY"),
            "source_summary": payload.get("source_summary", "manual_or_pending_sources"),
            "operator_notes": payload.get("operator_notes", ""),
            "image_reference": payload.get("image_reference", ""),
            "map_link": payload.get("map_link", ""),
        }
    )
    return row


def write_reports(rows: list[dict[str, Any]], mode: str = "dry-run", output_dir: Path = REPORT_DIR) -> dict[str, Any]:
    validated = [validate_report_row(row) for row in rows]
    if any(item["status"] != "REPORT_ROW_READY" for item in validated):
        return {"status": "REPORT_SCHEMA_INVALID", "written": False, "validation": validated}
    targets = {
        "csv": str(output_dir / "vegetation_risk_report.csv"),
        "json": str(output_dir / "latest_vegetation_risk_report.json"),
    }
    if mode != "write":
        return {"status": "REPORT_DRY_RUN_READY", "rows": len(rows), "targets": targets, "written": False}
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "vegetation_risk_report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    latest_path = output_dir / "latest_vegetation_risk_report.json"
    latest_path.write_text(json.dumps(rows[-1] if rows else {}, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "REPORT_WRITTEN", "rows": len(rows), "targets": targets, "written": True}


def latest_report_status(output_dir: Path = REPORT_DIR) -> dict[str, Any]:
    latest_path = output_dir / "latest_vegetation_risk_report.json"
    if not latest_path.exists():
        return {"status": "LATEST_REPORT_NOT_READY", "path": str(latest_path)}
    return {"status": "LATEST_REPORT_READY", "path": str(latest_path)}
