"""Environmental data completeness checks without filling fake values."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT


REQUIRED_ENV_FIELDS = [
    "season",
    "rainfall_mm",
    "temperature_c",
    "relative_humidity_percent",
    "soil_moisture",
    "soil_ph",
    "solar_radiation",
    "evapotranspiration",
    "wind_speed",
]


def check_environmental_readiness(manual_csv: Path | None = None, values: dict[str, Any] | None = None) -> dict[str, Any]:
    manual_csv = manual_csv or PROJECT_ROOT / "data" / "templates" / "environmental_manual_template.csv"
    values = values or {}
    missing = [field for field in REQUIRED_ENV_FIELDS if values.get(field) in (None, "")]
    if not manual_csv.exists():
        status = "ENVIRONMENT_MANUAL_REQUIRED"
    elif missing:
        status = "ENVIRONMENT_PARTIAL"
    else:
        status = "ENVIRONMENT_READY"
    return {
        "status": status,
        "manual_csv_exists": manual_csv.exists(),
        "manual_csv": str(manual_csv),
        "open_meteo_status": "OPTIONAL_NOT_FETCHED",
        "nasa_power_status": "OPTIONAL_NOT_FETCHED",
        "soilgrids_status": "OPTIONAL_NOT_FETCHED",
        "cache_status": "CACHE_OPTIONAL",
        "missing_parameters": missing,
        "not_fake_environment": True,
    }
