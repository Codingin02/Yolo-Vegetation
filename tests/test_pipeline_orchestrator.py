from ulp_project.pipeline_orchestrator import run_pipeline_mode


def test_pipeline_orchestrator_all_dry_run():
    result = run_pipeline_mode("all-dry-run")
    assert result["status"] == "SYSTEM_RUNTIME_DRY_RUN_READY"
    assert "status" in result["results"]
    assert result["results"]["risk-dry-run"]["status"] == "ENVIRONMENTAL_DATA_NOT_READY"
