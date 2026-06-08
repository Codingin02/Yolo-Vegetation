from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_remote_realtime_server as remote_server


def test_progress6_9_frame_endpoint_live_app_no_404_405_500(tmp_path) -> None:
    client = remote_server.create_app(runtime_root=tmp_path).test_client()
    session_id = client.post("/api/field/session/start", json={"point_id": "V001_pohon_sono"}).get_json()["session_id"]
    cases = [
        {"session_id": session_id, "frame_image_base64": ""},
        {"session_id": session_id, "frame_image_base64": "not-base64"},
        {"session_id": session_id, "frame_image_base64": "data:image/jpeg;base64,////"},
    ]
    for payload in cases:
        response = client.post("/api/field/session/frame", json=payload)
        assert response.status_code not in {404, 405, 500}
        assert response.get_json()["status"] in {
            "FRAME_SKIPPED_NO_IMAGE",
            "FRAME_DECODE_FAILED_SAFE",
            "TREE_MODEL_INFERENCE_FAILED_SAFE",
            "REALTIME_YOLO_PIPELINE_OK",
        }

    missing = client.post("/api/field/session/frame", json={"frame_image_base64": ""})
    assert missing.status_code == 400
    assert missing.get_json()["status"] == "FIELD_SESSION_ID_REQUIRED"
