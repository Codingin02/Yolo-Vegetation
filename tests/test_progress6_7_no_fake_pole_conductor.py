from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_7_frame_never_fakes_pole_conductor(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    session = client.post("/api/field/session/start", json={"source_mode": "SMOKE_TEST"}).get_json()["session_id"]
    response = client.post("/api/field/session/frame", json={"session_id": session, "frame_image_base64": "%%%bad"})
    payload = response.get_json()
    assert payload["pole_detected"] is False
    assert payload["conductor_detected"] is False
    assert payload["pole_model_status"] == "POLE_MODEL_NOT_READY"
    assert payload["conductor_model_status"] == "CONDUCTOR_MODEL_NOT_READY"
    assert payload["no_fake_pole_conductor_detection"] is True
