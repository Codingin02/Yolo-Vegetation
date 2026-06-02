from ulp_project.spreadsheet_report_writer import build_phase8_report_row, write_phase8_report
from ulp_project.spreadsheet_schema import PHASE8_SPREADSHEET_COLUMNS, validate_phase8_row


def test_phase8_spreadsheet_schema_has_required_columns():
    for column in [
        "timestamp",
        "point_id",
        "minimum_clearance_m",
        "days_to_contact_p50",
        "months_to_contact_p50",
        "risk_priority",
        "recommended_action",
        "model_status",
        "calibration_status",
        "environmental_data_status",
    ]:
        assert column in PHASE8_SPREADSHEET_COLUMNS
    row = build_phase8_report_row({"point_id": "V001_pohon_sono"})
    assert validate_phase8_row(row)["status"] == "SPREADSHEET_ROW_READY"
    assert write_phase8_report([row], mode="dry-run")["status"] == "SPREADSHEET_REPORT_DRY_RUN_READY"
