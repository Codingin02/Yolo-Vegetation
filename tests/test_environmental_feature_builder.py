from ulp_project.environmental_feature_builder import build_phase7_environmental_features, classify_season_from_rainfall


def test_environmental_builder_does_not_fake_missing_data():
    result = build_phase7_environmental_features({})
    assert result["status"] == "ENVIRONMENTAL_DATA_NOT_READY"
    assert result["season_status"] == "UNKNOWN_SEASON"


def test_rainfall_proxy_season():
    result = classify_season_from_rainfall({"rainfall_mm_30d": 200})
    assert result["season_status"] == "RAINFALL_PROXY_SEASON"
    assert result["season_label"] == "rainy_proxy"
