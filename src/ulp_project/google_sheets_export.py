"""Google Sheets-ready local export facade without live credentials."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .phase9_monitoring import MONITORING_CSV


SHEET_GROUPS = ["Inspections", "Risk Summary", "Environmental Inputs", "Asset Clearance", "Action Queue"]


def google_sheets_status(credentials_path: Path | None = None) -> dict[str, Any]:
    if credentials_path is None or not credentials_path.exists():
        return {
            "status": "GOOGLE_SHEETS_NOT_CONFIGURED",
            "local_csv": str(MONITORING_CSV),
            "sheet_groups": SHEET_GROUPS,
            "reason": "No credential path provided. Keep local CSV first; do not commit credentials.",
        }
    return {"status": "GOOGLE_SHEETS_CREDENTIAL_AVAILABLE_NOT_PUSHED", "credential_path": str(credentials_path), "sheet_groups": SHEET_GROUPS}


def export_google_sheets_ready_csv(mode: str = "dry-run") -> dict[str, Any]:
    return {
        "status": "GOOGLE_SHEETS_READY_CSV_DRY_RUN" if mode != "write" else "GOOGLE_SHEETS_READY_CSV_LOCAL_ONLY",
        "local_csv": str(MONITORING_CSV),
        "sheet_groups": SHEET_GROUPS,
        "live_push": False,
        "credential_status": google_sheets_status()["status"],
    }
