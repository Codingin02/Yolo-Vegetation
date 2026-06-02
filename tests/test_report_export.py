from ulp_project.report_export import build_operator_report, export_report


def test_report_export_dry_run_targets_outputs_reports():
    report = build_operator_report()
    result = export_report(report, mode="dry-run")
    assert result["status"] == "SYSTEM_REPORT_DRY_RUN_READY"
    assert "outputs" in result["targets"]["json"]
    assert "reports" in result["targets"]["json"]
    assert "No fake accuracy" in report["disclaimer"]
