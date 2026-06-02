from pathlib import Path

from ulp_project.environmental_features import build_environmental_feature_vector
from ulp_project.environmental_data import load_phase6_environmental_manual_csv
from ulp_project.soil_grid import build_soil_grid_features
from ulp_project.weather_grid import build_weather_grid_features


def test_environmental_feature_vector_reports_missing_without_fake_values():
    result = build_environmental_feature_vector({"point_id": "V001_pohon_sono"})
    assert result["status"] == "ENVIRONMENTAL_FEATURES_PARTIAL"
    assert "soil_ph" in result["missing_features"]
    assert result["features"]["soil_ph"] is None


def test_weather_and_soil_grids_need_coordinates_or_payload():
    assert build_weather_grid_features(None, None)["status"] == "WEATHER_GRID_NOT_READY"
    assert build_soil_grid_features(None, None)["status"] == "SOIL_GRID_NOT_READY"
    weather = build_weather_grid_features(-7.0, 112.0, {"rainfall_7d_mm": 20})
    assert weather["status"] == "WEATHER_GRID_PARTIAL"
    assert weather["features"]["rainfall_7d_mm"] == 20


def test_phase6_manual_environmental_template_is_parseable():
    result = load_phase6_environmental_manual_csv(Path("data/templates/environmental_manual_template.csv"))
    assert result["status"] == "READY"
