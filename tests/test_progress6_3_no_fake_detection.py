from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_3_model_not_ready_has_no_fake_detection(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    client.post("/api/field/session/start", json={"session_id": "NO_FAKE_DETECTION_TEST"})
    frame = client.post(
        "/api/field/session/frame",
        json={"session_id": "NO_FAKE_DETECTION_TEST", "point_id": "V001_pohon_sono"},
    ).get_json()
    if frame["model_status"] == "MODEL_NOT_READY":
        assert frame["detections"] == []
        assert frame["no_fake_detection"] is True
