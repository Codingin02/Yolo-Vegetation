from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.phase5_2_field_trial import (  # noqa: E402
    PHASE5_2_REPORT_COLUMNS,
    build_manual_prediction,
    build_report_row,
    write_field_trial_map,
    write_field_trial_snapshot_report,
)


def build_smoke_status(*, report_only: bool = False, map_only: bool = False) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        report_csv = tmp / "phase5_2_snapshot.csv"
        map_html = tmp / "phase5_2_map.html"
        no_gps_payload = {
            "point_id": "V001_pohon_sono",
            "clearance_m": 5.0,
            "growth_rate_m_per_day": 0.01,
            "measurement_source": "manual",
        }
        with_gps_payload = {
            **no_gps_payload,
            "latitude": -7.0,
            "longitude": 112.0,
            "gps_source": "test_internal",
            "notes": "TEST_INTERNAL_NOT_FIELD_DATA",
        }
        no_gps_report = write_field_trial_snapshot_report(no_gps_payload, output=report_csv, map_output=map_html)
        dummy_gps_report = write_field_trial_snapshot_report(with_gps_payload, output=report_csv, map_output=map_html)
        prediction = build_manual_prediction(no_gps_payload)
        row = build_report_row(prediction, report_id="schema_smoke", timestamp="2026-06-04T00:00:00")
        no_gps_map = write_field_trial_map(row, tmp / "no_gps_map.html")

        checks = {}
        if not map_only:
            checks.update(
                {
                    "report_written_only_on_snapshot": no_gps_report.get("report_written") is True,
                    "report_csv_exists": report_csv.exists(),
                    "report_schema_has_required_columns": set(PHASE5_2_REPORT_COLUMNS).issubset(set(row)),
                    "google_sheets_local_ready_status": no_gps_report.get("google_sheets_status") == "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY",
                }
            )
        if not report_only:
            checks.update(
                {
                    "no_gps_no_marker": no_gps_map["written"] is False and no_gps_map["status"] == "NO_GPS_NO_MARKER",
                    "snapshot_without_gps_no_marker": no_gps_report.get("map_status") == "NO_GPS_NO_MARKER",
                    "dummy_gps_marked_test_internal": dummy_gps_report.get("map_status") == "TEST_INTERNAL_NOT_FIELD_DATA",
                    "map_file_written_for_dummy_gps": Path(dummy_gps_report.get("map_path", "")).exists(),
                }
            )
        passed = all(checks.values())
        return {
            "status": "PHASE5_2_REPORT_MAP_SMOKE_PASS" if passed else "PHASE5_2_REPORT_MAP_SMOKE_FAIL",
            "checks": checks,
            "no_gps_report": {k: no_gps_report.get(k) for k in ("report_written", "report_csv_path", "map_status", "map_marker_written")},
            "dummy_gps_report": {k: dummy_gps_report.get(k) for k in ("report_written", "map_status", "map_marker_written")},
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Progress 5.2 report/map smoke test.")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--map-only", action="store_true")
    args = parser.parse_args(argv)
    result = build_smoke_status(report_only=args.report_only, map_only=args.map_only)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
