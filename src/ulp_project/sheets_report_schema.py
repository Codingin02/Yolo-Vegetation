"""Google Sheets/CSV vegetation risk report schema."""

from __future__ import annotations

REPORT_COLUMNS = [
    "report_id",
    "timestamp_wib",
    "point_id",
    "gps_lat",
    "gps_lon",
    "address_or_area",
    "species",
    "detected_object",
    "nearest_electrical_asset",
    "span_id",
    "pole_pair_id",
    "tree_height_m",
    "tree_height_confidence",
    "clearance_to_asset_m",
    "clearance_confidence",
    "season_label",
    "rainfall_mm_7d",
    "rainfall_mm_30d",
    "temperature_c_mean_30d",
    "humidity_mean_30d",
    "soil_ph",
    "soil_moisture_proxy",
    "growth_rate_m_per_day_min",
    "growth_rate_m_per_day_mid",
    "growth_rate_m_per_day_max",
    "eta_days_min",
    "eta_days_mid",
    "eta_days_max",
    "eta_months_mid",
    "risk_status",
    "recommended_action",
    "priority_rank",
    "model_status",
    "calibration_status",
    "environmental_data_status",
    "data_quality_flags",
    "source_summary",
    "operator_notes",
    "image_reference",
    "map_link",
]


def empty_report_row() -> dict[str, str]:
    return {column: "" for column in REPORT_COLUMNS}


def validate_report_row(row: dict[str, object]) -> dict[str, object]:
    missing = [column for column in REPORT_COLUMNS if column not in row]
    return {"status": "REPORT_ROW_READY" if not missing else "REPORT_ROW_SCHEMA_INCOMPLETE", "missing_columns": missing}
