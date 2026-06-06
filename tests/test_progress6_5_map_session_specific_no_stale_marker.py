from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_5_map_is_session_specific_and_has_no_legacy_fallback(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    client.post(
        "/api/field/session/start",
        json={"session_id": "P65_MAP_A", "source_mode": "SMOKE_TEST"},
    )
    client.post(
        "/api/field/session/gps-update",
        json={"session_id": "P65_MAP_A", "latitude": -7.1234567, "longitude": 112.7654321, "accuracy": 8},
    )

    result = client.get("/api/field/session/P65_MAP_A/map").get_json()
    html = client.get("/field-map/session/P65_MAP_A").get_data(as_text=True)

    assert result["status"] == "MAP_HTML_READY"
    assert result["field_map_url"] == "/field-map/session/P65_MAP_A"
    assert "progress5_4_fallback" not in result
    assert "P65_MAP_A" in html
    assert "-7.1234567" in html
    assert "112.7654321" in html
