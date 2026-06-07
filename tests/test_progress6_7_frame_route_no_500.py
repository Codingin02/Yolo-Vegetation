from __future__ import annotations

import base64

from ulp_project.flask_app import create_app


PNG_1X1 = "data:image/png;base64," + "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="


def test_progress6_7_frame_route_returns_json_not_500(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    started = client.post("/api/field/session/start", json={"source_mode": "SMOKE_TEST"}).get_json()
    session_id = started["session_id"]

    responses = [
        client.post("/api/field/session/frame", json={"session_id": session_id, "frame_image_base64": PNG_1X1}),
        client.post("/api/field/session/frame", json={"session_id": session_id, "frame_image_base64": "%%%bad"}),
        client.post("/api/field/session/frame", json={"session_id": session_id}),
        client.post("/api/field/session/frame", json={"frame_image_base64": PNG_1X1}),
    ]

    assert all(response.status_code != 500 for response in responses)
    assert responses[1].get_json()["status"] == "FRAME_DECODE_FAILED_SAFE"
    assert responses[2].get_json()["status"] == "FRAME_SKIPPED_NO_IMAGE"
    assert responses[3].status_code == 400
    assert responses[3].get_json()["status"] == "FIELD_SESSION_ID_REQUIRED"
