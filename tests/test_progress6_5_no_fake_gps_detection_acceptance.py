from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_5_model_not_ready_still_has_empty_detections_and_no_fake_gps(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    client.post("/api/field/session/start", json={"session_id": "P65_NO_FAKE", "source_mode": "SMOKE_TEST"})
    frame = client.post("/api/field/session/frame", json={"session_id": "P65_NO_FAKE"}).get_json()
    map_result = client.get("/api/field/latest-map?session_id=P65_NO_FAKE").get_json()

    assert frame["model_status"] == "MODEL_NOT_READY"
    assert frame["detections"] == []
    assert frame["no_fake_detection"] is True
    assert map_result["status"] == "NO_GPS_NO_MARKER"
    assert map_result["map_exists"] is True
