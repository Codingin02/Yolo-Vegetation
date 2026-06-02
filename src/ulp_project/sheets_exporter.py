"""Safe Google Sheets exporter facade.

Live Google Sheets push is disabled unless credentials are explicitly provided
outside the repository. CSV remains the primary local monitoring output.
"""

from __future__ import annotations

import os
from typing import Any


def export_to_google_sheets(rows: list[dict[str, Any]], spreadsheet_id: str | None = None, mode: str = "dry-run") -> dict[str, Any]:
    credential = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if mode != "live":
        return {"status": "SHEETS_DRY_RUN_READY", "rows": len(rows), "written": False}
    if not credential or not spreadsheet_id:
        return {"status": "SHEETS_NOT_CONFIGURED", "rows": len(rows), "written": False}
    return {"status": "SHEETS_LIVE_NOT_IMPLEMENTED_IN_PHASE7", "rows": len(rows), "written": False}
