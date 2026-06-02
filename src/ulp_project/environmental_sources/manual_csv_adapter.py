"""Manual environmental CSV adapter for Phase 7."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def load_manual_environmental_rows(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "MANUAL_ENV_CSV_NOT_READY", "rows": []}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {"status": "MANUAL_ENV_CSV_READY", "rows": rows}
