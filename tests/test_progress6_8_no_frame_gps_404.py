from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_8_frame_and_gps_routes_not_404_405_500(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    start = client.post("/api/field/session/start", json={"idempotency_key": "P68_NO_404"}).get_json()
    session_id = start["session_id"]
    frame = client.post("/api/field/session/frame", json={"session_id": session_id, "frame_image_base64": "bad"})
    gps = client.post(
        "/api/field/session/gps-update",
        json={"session_id": session_id, "latitude": -7.2161234, "longitude": 112.7351234, "accuracy": 6.7},
    )
    assert frame.status_code not in {404, 405, 500}
    assert gps.status_code not in {404, 405, 500}
    assert frame.get_json()["status"] in {"FRAME_DECODE_FAILED_SAFE", "TREE_MODEL_INFERENCE_FAILED_SAFE", "REALTIME_YOLO_PIPELINE_OK"}
    assert gps.get_json()["status"] in {"GPS_UPDATED", "DISTANCE_NOT_AVAILABLE", "GPS_INVALID_SAFE", "DISTANCE_NOT_RELIABLE_ACCURACY_GT_DISTANCE"}
