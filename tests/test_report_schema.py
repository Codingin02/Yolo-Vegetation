from ulp_project.sheets_exporter import export_to_google_sheets
from ulp_project.sheets_report_schema import REPORT_COLUMNS, empty_report_row, validate_report_row
from ulp_project.vegetation_report_writer import build_report_row, write_reports


def test_report_schema_complete_and_dry_run_no_live_sheets():
    assert "eta_months_mid" in REPORT_COLUMNS
    assert "risk_status" in REPORT_COLUMNS
    row = build_report_row({"point_id": "V001_pohon_sono"})
    assert validate_report_row(row)["status"] == "REPORT_ROW_READY"
    assert write_reports([row], mode="dry-run")["status"] == "REPORT_DRY_RUN_READY"
    assert export_to_google_sheets([row], mode="live")["status"] == "SHEETS_NOT_CONFIGURED"


def test_empty_report_row_has_all_columns():
    row = empty_report_row()
    assert set(REPORT_COLUMNS) == set(row)
