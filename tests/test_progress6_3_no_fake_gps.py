from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_3_missing_gps_is_not_faked(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    started = client.post("/api/field/session/start", json={"session_id": "NO_FAKE_GPS_TEST"}).get_json()
    assert started["no_fake_gps"] is True
    assert started["derived_gps"]["horizontal_distance_from_tree_m"] is None
    assert started["derived_gps"]["distance_reliability_status"] == "DISTANCE_NOT_AVAILABLE"
    latest_map = client.get("/api/field/latest-map?session_id=NO_FAKE_GPS_TEST").get_json()
    assert latest_map["status"] == "NO_GPS_NO_MARKER"
