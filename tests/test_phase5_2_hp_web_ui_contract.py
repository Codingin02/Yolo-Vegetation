from __future__ import annotations

from ulp_project.flask_app import create_app


def test_phase5_2_field_capture_ui_contains_required_controls() -> None:
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)
    for token in [
        "server-status",
        "model-status",
        "calibration-status",
        "realtime-transport-status",
        "secure-context-status",
        "gps-status",
        "camera-status",
        "tunnel-status",
        "manual-prediction",
        "snapshot-report",
        "copy-report-link",
        "open-map-report",
        "point_id",
        "V001_pohon_sono",
        "growth_rate_m_per_day",
        "measurement_source",
        "environment_source",
        "clearance_display_m_integer_floor",
    ]:
        assert token in html


def test_phase5_2_required_api_routes_exist() -> None:
    app = create_app()
    routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
    assert "/api/runtime/public-links" in routes
    assert "/api/runtime/status" in routes
    assert "/api/model/status" in routes
    assert "/api/calibration/status" in routes
    assert "/api/field/manual-prediction" in routes
    assert "/api/field/snapshot-report" in routes
    assert "/api/realtime/frame" in routes
    assert "/ws/realtime-detect" in routes
