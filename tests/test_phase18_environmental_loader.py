from ulp_project.environmental_manual_loader import validate_environmental_manual_csv
from ulp_project.environmental_source_registry import source_availability_summary


def test_environmental_manual_template_present():
    result = validate_environmental_manual_csv()
    assert result["status"] in {"MANUAL_ENVIRONMENT_READY", "ENVIRONMENT_MANUAL_TEMPLATE_PARTIAL"}
    assert result["missing_columns"] == []


def test_environment_source_registry_no_api_required():
    assert source_availability_summary()["no_api_key_required"] is True
