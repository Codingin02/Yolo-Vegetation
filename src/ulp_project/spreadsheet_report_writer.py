"""CSV/XLSX-ready writer for Phase 8 vegetation risk monitoring."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .spreadsheet_schema import PHASE8_SPREADSHEET_COLUMNS, empty_phase8_row, validate_phase8_row

REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
CSV_PATH = REPORT_DIR / "vegetation_risk_report.csv"
XLSX_PATH = REPORT_DIR / "vegetation_risk_report.xlsx"


def build_phase8_report_row(payload: dict[str, Any]) -> dict[str, Any]:
    row = empty_phase8_row()
    row.update(
        {
            "timestamp": payload.get("timestamp") or datetime.now().isoformat(),
            "point_id": payload.get("point_id", "V001_pohon_sono"),
            "inspection_id": payload.get("inspection_id", ""),
            "operator_name": payload.get("operator_name", ""),
            "species": payload.get("species", "pohon_sono"),
            "detected_classes": payload.get("detected_classes", "MODEL_NOT_READY"),
            "gps_lat": payload.get("gps_lat", ""),
            "gps_lon": payload.get("gps_lon", ""),
            "region": payload.get("region", "Surabaya Utara - Perak"),
            "asset_type": payload.get("asset_type", "span"),
            "pole_id": payload.get("pole_id", ""),
            "span_id": payload.get("span_id", ""),
            "tree_height_m": payload.get("tree_height_m", ""),
            "asset_height_m": payload.get("asset_height_m", ""),
            "horizontal_distance_m": payload.get("horizontal_distance_m", ""),
            "vertical_clearance_m": payload.get("vertical_clearance_m", ""),
            "minimum_clearance_m": payload.get("minimum_clearance_m", ""),
            "clearance_status": payload.get("clearance_status", "INSUFFICIENT_DATA"),
            "season_label": payload.get("season_label", "unknown"),
            "rainfall_7d_mm": payload.get("rainfall_7d_mm", ""),
            "rainfall_30d_mm": payload.get("rainfall_30d_mm", ""),
            "temperature_avg_c": payload.get("temperature_avg_c", ""),
            "humidity_avg_percent": payload.get("humidity_avg_percent", ""),
            "soil_ph": payload.get("soil_ph", ""),
            "growth_rate_base_m_per_day": payload.get("growth_rate_base_m_per_day", ""),
            "growth_rate_adjusted_m_per_day": payload.get("growth_rate_adjusted_m_per_day", ""),
            "days_to_contact_p50": payload.get("days_to_contact_p50", ""),
            "months_to_contact_p50": payload.get("months_to_contact_p50", ""),
            "risk_priority": payload.get("risk_priority", "INSUFFICIENT_DATA"),
            "recommended_action": payload.get("recommended_action", "Lengkapi data kalibrasi/lingkungan"),
            "recommended_trim_deadline": payload.get("recommended_trim_deadline", "DATA_REQUIRED"),
            "confidence": payload.get("confidence", "LOW"),
            "model_status": payload.get("model_status", "MODEL_NOT_READY"),
            "calibration_status": payload.get("calibration_status", "CALIBRATION_NOT_READY"),
            "environmental_data_status": payload.get("environmental_data_status", "ENVIRONMENTAL_DATA_NOT_READY"),
            "photo_path": payload.get("photo_path", ""),
            "map_link": payload.get("map_link", ""),
            "notes": payload.get("notes", "No fake accuracy; final model waits for labels/training/calibration."),
        }
    )
    return row


def write_phase8_report(rows: list[dict[str, Any]], mode: str = "dry-run", output_dir: Path = REPORT_DIR) -> dict[str, Any]:
    validation = [validate_phase8_row(row) for row in rows]
    if any(item["status"] != "SPREADSHEET_ROW_READY" for item in validation):
        return {"status": "SPREADSHEET_SCHEMA_INVALID", "written": False, "validation": validation}
    targets = {"csv": str(output_dir / CSV_PATH.name), "xlsx": str(output_dir / XLSX_PATH.name)}
    if mode != "write":
        return {"status": "SPREADSHEET_REPORT_DRY_RUN_READY", "rows": len(rows), "written": False, "targets": targets}
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / CSV_PATH.name
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PHASE8_SPREADSHEET_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    xlsx_status = "XLSX_SKIPPED_OPENPYXL_NOT_AVAILABLE"
    try:
        import openpyxl
    except ImportError:
        pass
    else:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "vegetation_risk"
        sheet.append(PHASE8_SPREADSHEET_COLUMNS)
        for row in rows:
            sheet.append([row.get(column, "") for column in PHASE8_SPREADSHEET_COLUMNS])
        workbook.save(output_dir / XLSX_PATH.name)
        xlsx_status = "XLSX_READY"
    return {"status": "SPREADSHEET_REPORT_WRITTEN", "rows": len(rows), "written": True, "targets": targets, "xlsx_status": xlsx_status}
