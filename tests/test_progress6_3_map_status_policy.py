from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_3_map_no_gps_has_page_without_marker(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    client.post("/api/field/session/start", json={"session_id": "MAP_NO_GPS"})
    result = client.get("/api/field/latest-map?session_id=MAP_NO_GPS").get_json()
    assert result["status"] == "NO_GPS_NO_MARKER"
    assert result["map_exists"] is True
    assert result["map_url"].endswith("field_session_latest_map.html")


def test_progress6_3_map_valid_gps_has_marker_evidence(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    client.post("/api/field/session/start", json={"session_id": "MAP_WITH_GPS"})
    client.post(
        "/api/field/session/gps-update",
        json={"session_id": "MAP_WITH_GPS", "latitude": -7.1, "longitude": 110.2, "accuracy": 6},
    )
    result = client.get("/api/field/latest-map?session_id=MAP_WITH_GPS").get_json()
    assert result["status"] == "MAP_HTML_READY"
    assert result["google_maps_status"] == "GOOGLE_MAPS_NOT_CONFIGURED"
