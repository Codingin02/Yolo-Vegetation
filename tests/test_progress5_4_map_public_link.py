from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress5_4_map_link_serves_over_same_public_tunnel_path(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    no_gps = client.post("/api/field/shutter-capture", json={"point_id": "V001_pohon_sono", "model_status": "MODEL_NOT_READY"}).get_json()
    with_gps = client.post(
        "/api/field/shutter-capture",
        json={"point_id": "V001_pohon_sono", "gps_lat": -7.1, "gps_lon": 112.7, "gps_accuracy_m": 9, "gps_source": "GPS_SOURCE_BROWSER", "model_status": "MODEL_NOT_READY"},
    ).get_json()

    assert no_gps["map_status"] == "NO_GPS_NO_MARKER"
    assert with_gps["map_status"] == "MAP_MARKER_WRITTEN"
    assert with_gps["map_url"].startswith("/field-maps/")
    assert client.get(with_gps["map_url"]).status_code == 200
