from __future__ import annotations

import csv

from ulp_project.environmental_feature_engine import MANUAL_TEMPLATE, REQUIRED_ENV_OUTPUTS, build_environmental_features


def test_environmental_manual_template_has_phase15_columns() -> None:
    with MANUAL_TEMPLATE.open(newline="", encoding="utf-8") as handle:
        fieldnames = csv.DictReader(handle).fieldnames or []
    assert all(field in fieldnames for field in ["point_id", "latitude", "longitude", "date", *REQUIRED_ENV_OUTPUTS, "source_note"])


def test_environmental_engine_does_not_fabricate_when_offline() -> None:
    result = build_environmental_features(point_id="missing_point")
    assert result["status"] == "ENVIRONMENT_FEATURES_PARTIAL"
    assert result["not_fake_environment"] is True
    assert result["features"]["soil_ph"] is None
    assert result["adapters"]["open_meteo_optional"]["status"] == "SOURCE_NOT_AVAILABLE"
