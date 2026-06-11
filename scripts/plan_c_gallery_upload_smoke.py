from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.plan_c_storage import read_json, session_file  # noqa: E402


def main() -> int:
    app = create_app()
    client = app.test_client()
    start = client.post("/api/plan-c/session/start", json={})
    _assert(start.status_code == 201, "session start failed")
    session_id = start.get_json()["session_id"]
    payload = _mock_payload()
    image = _jpeg_bytes(1000, 1600)

    response = client.post(
        "/api/plan-c/session/snapshot",
        data={
            "session_id": session_id,
            "capture_source": "gallery",
            "mock_detection_payload": json.dumps(payload),
            "tree_anchor_gps": json.dumps({"latitude": -7.231, "longitude": 112.735, "accuracy_m": 5}),
            "shutter_gps": json.dumps({"latitude": -7.23105, "longitude": 112.73504, "accuracy_m": 6}),
            "gps_accuracy_m": "6",
            "snapshot": (BytesIO(image), "gallery.jpg"),
        },
        content_type="multipart/form-data",
    )
    _assert(response.status_code in {200, 201, 202}, f"snapshot failed: {response.status_code} {response.get_data(as_text=True)}")
    result = read_json(session_file(session_id, "result.json"), default={})
    metadata = read_json(session_file(session_id, "metadata.json"), default={})
    _assert(result.get("status") == "PLAN_C_RESULT_READY", "result not ready")
    _assert(metadata.get("capture_source") == "gallery", "gallery source not stored")
    _assert(session_file(session_id, "original.jpg").exists(), "original missing")
    _assert(session_file(session_id, "annotated.jpg").exists(), "annotated missing")
    _assert(result.get("detection_count", 0) >= 3, "mock detections not processed")
    _assert(result.get("gps_distance_from_anchor_m") is not None, "GPS distance not stored in result")
    _assert(result.get("prediction_days") is not None, "prediction days missing")
    _assert(result.get("prediction_window") != "data tidak cukup", "prediction window still insufficient")

    print("PLAN_C_GALLERY_UPLOAD_SMOKE_PASS")
    print(f"session_id={session_id}")
    print(f"risk_status={result.get('risk_status')}")
    print(f"prediction_window={result.get('prediction_window')}")
    return 0


def _mock_payload() -> dict[str, object]:
    return {
        "status": "DETECTION_READY",
        "image_quality": "clear",
        "detections": [
            {"class_name": "struktur_penyangga", "bbox_xyxy": [100, 200, 180, 1200], "confidence": 0.92, "review_status": "ACCEPT", "reason": "utility pole"},
            {"class_name": "konduktor", "bbox_xyxy": [50, 340, 950, 360], "confidence": 0.9, "review_status": "ACCEPT", "reason": "overhead conductor"},
            {"class_name": "konduktor", "bbox_xyxy": [50, 380, 950, 400], "confidence": 0.9, "review_status": "ACCEPT", "reason": "overhead conductor"},
            {"class_name": "pohon_sono", "bbox_xyxy": [400, 820, 720, 1200], "confidence": 0.91, "review_status": "ACCEPT", "reason": "pohon sono visible"},
        ],
    }


def _jpeg_bytes(width: int, height: int) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (width, height), (120, 170, 120))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
