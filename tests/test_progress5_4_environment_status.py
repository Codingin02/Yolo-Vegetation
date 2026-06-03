from __future__ import annotations

from ulp_project.environment import build_environment_status


def test_progress5_4_environment_does_not_fabricate_soil_or_rainfall() -> None:
    result = build_environment_status()

    assert result["environment_status"] == "ENVIRONMENT_NOT_AVAILABLE"
    assert result["rainfall_source"] == "RAINFALL_DATA_NOT_AVAILABLE"
    assert result["soil_source"] == "SOIL_DATA_NOT_AVAILABLE"
    assert result["soil_ph_status"] == "SOIL_DATA_NOT_AVAILABLE"
    assert result["no_fabricated_environment_data"] is True
