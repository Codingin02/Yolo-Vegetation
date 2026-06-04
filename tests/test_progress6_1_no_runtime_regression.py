from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_1_does_not_regress_progress5_4_runtime_contract() -> None:
    client = create_app().test_client()

    assert client.get("/favicon.ico").status_code == 204
    realtime = client.post("/api/field/realtime-frame", json={"point_id": "V001_pohon_sono"}).get_json()
    assert realtime["model_status"] == "MODEL_NOT_READY"
    assert realtime["detections"] == []
    assert realtime["no_fake_detection"] is True
    assert client.get("/field-capture").status_code == 200
