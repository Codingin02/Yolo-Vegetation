"""Manual CSV environmental loader. Does not fabricate missing values."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

DEFAULT_TEMPLATE = PROJECT_ROOT / "data" / "templates" / "environmental_manual_template.csv"
REQUIRED_ENV_COLUMNS = [
    "timestamp",
    "location_name",
    "latitude",
    "longitude",
    "season",
    "rainfall_mm_day",
    "rainfall_mm_7d",
    "temperature_c",
    "relative_humidity_percent",
    "soil_ph",
    "soil_moisture",
    "solar_radiation",
    "wind_speed",
    "source_name",
    "source_url",
    "operator_notes",
]


def validate_environmental_manual_csv(path: Path = DEFAULT_TEMPLATE) -> dict[str, Any]:
    if not path.exists():
        return {"status": "ENVIRONMENT_MANUAL_TEMPLATE_NOT_FOUND", "missing_columns": REQUIRED_ENV_COLUMNS}
    with path.open(newline="", encoding="utf-8") as handle:
        fieldnames = csv.DictReader(handle).fieldnames or []
    missing = [name for name in REQUIRED_ENV_COLUMNS if name not in fieldnames]
    return {"status": "MANUAL_ENVIRONMENT_READY" if not missing else "ENVIRONMENT_MANUAL_TEMPLATE_PARTIAL", "missing_columns": missing, "columns": fieldnames}


def load_manual_environment_rows(path: Path = DEFAULT_TEMPLATE) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
