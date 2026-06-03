from ulp_project.google_sheets_ready_export import FINAL_SHEETS_COLUMNS, export_google_sheets_ready_schema


def test_google_sheets_ready_schema_complete_without_credentials():
    result = export_google_sheets_ready_schema()
    assert result["sheets_status"] == "SHEETS_CREDENTIAL_NOT_CONFIGURED"
    assert "report_id" in FINAL_SHEETS_COLUMNS
    assert "measurement_quality_score" in FINAL_SHEETS_COLUMNS
