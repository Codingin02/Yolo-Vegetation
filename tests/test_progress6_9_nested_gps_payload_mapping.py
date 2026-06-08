from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_9_nested_gps_payload_maps_base_and_current(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    response = client.post(
        "/api/field/session/start",
        json={
            "point_id": "V001_pohon_sono",
            "operator_name": "debug_ps",
            "notes": "direct backend test",
            "gps": {"latitude": -7.2234567, "longitude": 112.7312345, "accuracy": 5.0},
        },
    )
    data = response.get_json()
    base = data["gps"]["base"]
    assert response.status_code in {201, 202}
    assert data["ok"] is True
    assert base["latitude"] == -7.2234567
    assert base["longitude"] == 112.7312345
    assert base["accuracy"] == 5.0
    assert base["gps_precision_status"] != "INVALID_COORDINATE_NULL"


def test_progress6_9_gps_update_accepts_nested_current_payload(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    session_id = client.post("/api/field/session/start", json={"point_id": "V001_pohon_sono"}).get_json()["session_id"]
    response = client.post(
        "/api/field/session/gps-update",
        json={
            "session_id": session_id,
            "gps": {"current": {"latitude": -7.2234568, "longitude": 112.7312346, "accuracy": 4.9}},
            "source": "browser_watchPosition",
        },
    )
    data = response.get_json()
    assert response.status_code not in {404, 405, 500}
    assert data["gps"]["latitude"] == -7.2234568
    assert data["gps"]["longitude"] == 112.7312346
    assert data["gps"]["accuracy"] == 4.9
