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


def load_manual_environmental_csv(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "ENVIRONMENTAL_DATA_NOT_READY", "rows": [], "missing_fields": ENVIRONMENTAL_FIELDS}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in ENVIRONMENTAL_FIELDS if field not in (reader.fieldnames or [])]
        rows = list(reader)
    return {"status": "READY" if not missing else "ENVIRONMENTAL_DATA_SCHEMA_INCOMPLETE", "rows": rows, "missing_fields": missing}
