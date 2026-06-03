from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.google_sheets_ready_export import FINAL_SHEETS_COLUMNS, export_google_sheets_ready_schema  # noqa: E402
from ulp_project.report_deduplicator import deduplicate_report  # noqa: E402
from ulp_project.report_snapshot_policy import should_write_snapshot_report  # noqa: E402


def main() -> int:
    schema = export_google_sheets_ready_schema()
    first = deduplicate_report({"session_id": "s", "point_id": "p", "risk_priority": "HIGH", "selected_clearance_m_stable": 2.5})
    second = deduplicate_report({"session_id": "s", "point_id": "p", "risk_priority": "HIGH", "selected_clearance_m_stable": 2.5})
    checks = {
        "schema_complete": all(col in schema["columns"] for col in ["report_id", "session_id", "eta_expected_days", "measurement_quality_score", "reason_codes"]),
        "local_csv_ready": schema["local_csv_status"] == "READY",
        "no_credentials_required": schema["sheets_status"] == "SHEETS_CREDENTIAL_NOT_CONFIGURED",
        "snapshot_policy": should_write_snapshot_report({"report_trigger": "MANUAL_SNAPSHOT"})["write_report"] is True,
        "dedup_cooldown": first["write_report"] is True and second["write_report"] is False,
        "columns_count": len(FINAL_SHEETS_COLUMNS) >= 40,
    }
    status = "PHASE19_REPORT_GATE_READY" if all(checks.values()) else "PHASE19_REPORT_GATE_FAIL"
    print(json.dumps({"status": status, "checks": checks, "schema": schema}, indent=2, ensure_ascii=False))
    print(status)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
