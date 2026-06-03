from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


ROOT = Path(__file__).resolve().parents[1]


def test_progress5_4_camera_ui_contains_shutter_overlay_and_no_primary_manual_clearance() -> None:
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)
    js = (ROOT / "src" / "ulp_project" / "static" / "field_capture.js").read_text(encoding="utf-8")

    for token in [
        "overlay-canvas",
        "shutter-capture",
        "Debug COCO Overlay",
        "tree-height-m",
        "pole-height-reference-m",
        "cable-height-m",
        "zone_status",
        "Advanced Debug Only",
        "manual-prediction",
        "growth_rate_m_per_day",
        "measurement_source",
        "environment_source",
        "clearance_display_m_integer_floor",
    ]:
        assert token in html
    assert "watchPosition" in js
    assert "/api/field/realtime-frame" in js
    assert "/api/field/shutter-capture" in js
    assert "Clearance (m)" not in html


def test_progress5_4_required_routes_exist() -> None:
    app = create_app()
    routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
    for route in [
        "/api/field/realtime-status",
        "/api/field/realtime-frame",
        "/api/field/shutter-capture",
        "/api/field/latest-measurement",
        "/api/field/report-latest",
        "/api/field/map-latest",
        "/api/field/gps-status",
        "/api/field/calibration-status",
        "/api/field/debug-coco-frame",
    ]:
        assert route in routes
