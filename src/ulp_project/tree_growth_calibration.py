"""Manual tree growth calibration CSV parser."""

from __future__ import annotations

import csv
from pathlib import Path

FIELDS = [
    "point_id",
    "species",
    "date_observed",
    "height_m",
    "canopy_width_m",
    "clearance_to_asset_m",
    "pruned_status",
    "notes",
    "measured_by",
]


def load_tree_growth_calibration_csv(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "CALIBRATION_DATA_NOT_READY", "rows": [], "missing_fields": FIELDS}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in FIELDS if field not in (reader.fieldnames or [])]
        rows = list(reader)
    return {"status": "READY" if not missing else "CALIBRATION_SCHEMA_INCOMPLETE", "rows": rows, "missing_fields": missing}
