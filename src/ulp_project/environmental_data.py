"""Manual environmental input loading for future risk scoring."""

from __future__ import annotations

import csv
from pathlib import Path


ENVIRONMENTAL_FIELDS = [
    "point_id",
    "vegetation_class",
    "current_tree_height_m",
    "current_clearance_m",
    "estimated_growth_cm_per_month",
    "rainfall_monthly_mm",
    "season_label",
    "soil_ph",
    "soil_type",
    "temperature_c",
    "humidity_percent",
    "pruning_history_date",
    "observation_date",
    "confidence_source",
]

PHASE6_ENVIRONMENTAL_FIELDS = [
    "point_id",
    "latitude",
    "longitude",
    "observation_date",
    "temperature_2m_c",
    "relative_humidity_2m_percent",
    "precipitation_mm",
    "rainfall_7d_mm",
    "rainfall_30d_mm",
    "dry_days_count_14d",
    "wind_speed_10m_ms",
    "wind_gust_ms",
    "solar_radiation",
    "soil_ph",
    "soil_clay_percent",
    "soil_sand_percent",
    "soil_silt_percent",
    "soil_organic_carbon",
    "soil_bulk_density",
    "soil_moisture_proxy",
    "elevation_m",
    "source_note",
]


def load_manual_environmental_csv(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "ENVIRONMENTAL_DATA_NOT_READY", "rows": [], "missing_fields": ENVIRONMENTAL_FIELDS}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in ENVIRONMENTAL_FIELDS if field not in (reader.fieldnames or [])]
        rows = list(reader)
    return {"status": "READY" if not missing else "ENVIRONMENTAL_DATA_SCHEMA_INCOMPLETE", "rows": rows, "missing_fields": missing}


def load_phase6_environmental_manual_csv(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "ENVIRONMENTAL_DATA_NOT_READY", "rows": [], "missing_fields": PHASE6_ENVIRONMENTAL_FIELDS}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing = [field for field in PHASE6_ENVIRONMENTAL_FIELDS if field not in fieldnames]
        rows = list(reader)
    phase8_required = [
        "point_id",
        "latitude",
        "longitude",
        "observation_date",
        "season_label",
        "rainfall_7d_mm",
        "rainfall_30d_mm",
        "temperature_avg_c",
        "humidity_avg_percent",
        "soil_ph",
        "soil_moisture_proxy",
        "wind_speed_avg",
        "data_source",
        "freshness_status",
        "source_confidence",
    ]
    if missing and all(field in fieldnames for field in phase8_required):
        return {"status": "READY", "rows": rows, "missing_fields": []}
    return {"status": "READY" if not missing else "ENVIRONMENTAL_DATA_SCHEMA_INCOMPLETE", "rows": rows, "missing_fields": missing}
