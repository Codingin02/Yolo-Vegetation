from ulp_project.risk_map_exporter import export_risk_map, row_to_geojson_feature


def test_risk_map_reports_missing_gps_without_fake_coordinates():
    result = row_to_geojson_feature({"point_id": "V001_pohon_sono"})
    assert result["status"] == "GPS_NOT_AVAILABLE"
    dry = export_risk_map([{"point_id": "V001_pohon_sono"}], mode="dry-run")
    assert dry["status"] == "RISK_MAP_DRY_RUN_READY"
    assert dry["gps_missing"] == 1


def test_risk_map_geojson_feature_with_real_coordinates():
    result = row_to_geojson_feature({"point_id": "V001", "gps_lat": "-7.1", "gps_lon": "112.7", "risk_status": "PERLU_MONITORING"})
    assert result["status"] == "GPS_READY"
    assert result["feature"]["geometry"]["coordinates"] == [112.7, -7.1]


def test_risk_map_accepts_phase8_priority_fields():
    result = row_to_geojson_feature(
        {
            "point_id": "V001",
            "gps_lat": "-7.1",
            "gps_lon": "112.7",
            "risk_priority": "HIGH",
            "months_to_contact_p50": 2,
            "minimum_clearance_m": 1.0,
        }
    )
    assert result["feature"]["properties"]["risk_priority"] == "HIGH"
