"""Phase 8 spreadsheet monitoring schema."""

from __future__ import annotations

PHASE8_SPREADSHEET_COLUMNS = [
    "timestamp",
    "point_id",
    "inspection_id",
    "operator_name",
    "species",
    "detected_classes",
    "gps_lat",
    "gps_lon",
    "region",
    "asset_type",
    "pole_id",
    "span_id",
    "tree_height_m",
    "asset_height_m",
    "horizontal_distance_m",
    "vertical_clearance_m",
    "minimum_clearance_m",
    "clearance_status",
    "season_label",
    "rainfall_7d_mm",
    "rainfall_30d_mm",
    "temperature_avg_c",
    "humidity_avg_percent",
    "soil_ph",
    "growth_rate_base_m_per_day",
    "growth_rate_adjusted_m_per_day",
    "days_to_contact_p50",
    "months_to_contact_p50",
    "risk_priority",
    "recommended_action",
    "recommended_trim_deadline",
    "confidence",
    "model_status",
    "calibration_status",
    "environmental_data_status",
    "photo_path",
    "map_link",
    "notes",
]


def empty_phase8_row() -> dict[str, str]:
    return {column: "" for column in PHASE8_SPREADSHEET_COLUMNS}


def validate_phase8_row(row: dict[str, object]) -> dict[str, object]:
    missing = [column for column in PHASE8_SPREADSHEET_COLUMNS if column not in row]
    return {"status": "SPREADSHEET_ROW_READY" if not missing else "SPREADSHEET_ROW_INCOMPLETE", "missing_columns": missing}
