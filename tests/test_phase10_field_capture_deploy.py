from __future__ import annotations

from ulp_project.flask_app import create_app


def test_phase10_network_routes_and_manual_upload_work() -> None:
    client = create_app().test_client()
    assert client.get("/field-capture").status_code == 200
    assert client.get("/api/network/whoami").status_code == 200
    assert client.get("/api/network/health").status_code == 200
    assert client.get("/api/latency/ping").status_code == 200

    response = client.post(
        "/api/field-capture/upload",
        json={
            "point_id": "V001_pohon_sono",
            "species": "pohon_sono",
            "asset_type": "span",
            "clearance_m": 5.0,
            "growth_rate_m_per_day": 0.01,
            "latitude": -7.0,
            "longitude": 112.0,
        },
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["eta_days"] == 200.0
    assert data["risk_priority"] == "LOW"
    assert data["model_status"] == "MODEL_NOT_READY"


def test_phase10_upload_missing_growth_is_insufficient() -> None:
    client = create_app().test_client()
    response = client.post("/api/field-capture/upload", json={"point_id": "V001_pohon_sono", "clearance_m": 5.0})
    data = response.get_json()
    assert response.status_code == 202
    assert data["status"] == "INSUFFICIENT_DATA"
    assert data["eta_days"] is None
