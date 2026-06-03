"""Google Sheets-ready schema/export status without live credential dependency."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .phase9_monitoring import MONITORING_CSV

FINAL_SHEETS_COLUMNS = [
    "report_id",
    "timestamp",
    "session_id",
    "frame_id_snapshot",
    "point_id",
    "object_id",
    "species",
    "class_name",
    "asset_type",
    "latitude",
    "longitude",
    "gps_accuracy_m",
    "tree_height_m",
    "asset_height_m",
    "span_lowest_point_height_m",
    "cable_height_m",
    "selected_clearance_m_raw",
    "selected_clearance_m_stable",
    "selected_clearance_display_m",
    "safe_clearance_min_m",
    "distance_zone_status",
    "eta_min_days",
    "eta_expected_days",
    "eta_max_days",
    "eta_expected_months",
    "risk_priority",
    "action_recommendation",
    "measurement_quality_score",
    "measurement_quality_label",
    "confidence_status",
    "model_status",
    "calibration_status",
    "environmental_data_status",
    "season",
    "rainfall_mm_day",
    "rainfall_mm_7d",
    "temperature_c",
    "relative_humidity_percent",
    "soil_ph",
    "soil_moisture",
    "growth_rate_base_m_per_day",
    "growth_rate_adjusted_m_per_day",
    "report_trigger",
    "map_marker_status",
    "image_evidence_path",
    "operator_notes",
    "reason_codes",
]


def google_sheets_ready_status(credentials_env: str = "GOOGLE_APPLICATION_CREDENTIALS") -> dict[str, Any]:
    cred = os.environ.get(credentials_env)
    if not cred:
        return {"sheets_status": "SHEETS_CREDENTIAL_NOT_CONFIGURED", "local_csv_status": "READY", "local_csv": str(MONITORING_CSV)}
    path = Path(cred)
    return {
        "sheets_status": "SHEETS_READY_DRY_RUN" if path.exists() else "SHEETS_CREDENTIAL_PATH_NOT_FOUND",
        "credential_path_runtime_only": str(path),
        "local_csv_status": "READY",
        "local_csv": str(MONITORING_CSV),
    }


def export_google_sheets_ready_schema(mode: str = "dry-run") -> dict[str, Any]:
    return {
        "status": "GOOGLE_SHEETS_READY_SCHEMA_LOCAL_ONLY",
        "mode": mode,
        "columns": FINAL_SHEETS_COLUMNS,
        **google_sheets_ready_status(),
        "no_live_push": True,
    }
