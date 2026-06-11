from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.plan_c_feedback_learning import ACCEPTED_JSONL, REJECTED_JSONL  # noqa: E402
from ulp_project.plan_c_storage import session_file  # noqa: E402


def main() -> int:
    app = create_app()
    client = app.test_client()
    checks: list[str] = []

    ready = _snapshot_with_mock(
        client,
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [
                _det("pohon_sono", [250, 170, 510, 450], 0.88, "pohon sono candidate"),
                _det("konduktor", [70, 120, 580, 145], 0.84, "overhead distribution conductor"),
                _det("struktur_penyangga", [30, 60, 85, 460], 0.81, "utility pole support"),
            ],
            "negative_findings": [],
            "warnings": [],
        },
        gps=True,
    )
    result = ready["result"]
    _assert(result["detection_status"] == "YOLO_COMPATIBLE_DETECTION_READY", "ready detection status")
    _assert(result["detection_count"] >= 3, "ready detection count")
    _assert(result["geometry_status"] != "INSUFFICIENT_GEOMETRY_DATA", "geometry ready")
    _assert(result["risk_status"] in {"AMAN", "PANTAU", "ZONA_TEBANG"}, "risk useful")
    _assert(result["prediction_window"] != "data tidak cukup", "prediction useful")
    _assert(result.get("zone_overlay_status") == "ZONE_OVERLAY_READY", "zone overlay ready")
    _assert(session_file(ready["session_id"], "annotated.jpg").exists(), "annotated created")
    checks.append("ready_tree_conductor_structure")

    human = _snapshot_with_mock(
        client,
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [
                _det("person", [100, 100, 300, 440], 0.9, "person face and body"),
                _det("face", [140, 110, 230, 210], 0.87, "face/head visible"),
            ],
            "negative_findings": [{"object": "person", "action": "ignored", "reason": "not a target object"}],
        },
        gps=False,
    )
    human_result = human["result"]
    _assert(human_result["detection_count"] == 0, "human no target bbox")
    _assert(human_result["risk_status"] == "DATA_TIDAK_CUKUP", "human risk data not enough")
    _assert(human_result.get("detections") == [], "human no false bbox")
    checks.append("human_false_positive_filter")

    non_sono = _snapshot_with_mock(
        client,
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [
                _det("tree", [250, 165, 520, 455], 0.8, "clear tree but species not confirmed"),
                _det("konduktor", [70, 120, 580, 145], 0.82, "overhead conductor"),
                _det("struktur_penyangga", [30, 60, 85, 460], 0.8, "utility pole"),
            ],
        },
        gps=False,
    )
    non_sono_result = non_sono["result"]
    _assert(non_sono_result["tree_species_status"] == "pohon_non_sono", "non-sono species")
    _assert(any(item["class_name"] == "pohon_non_sono" for item in non_sono_result["detections"]), "non-sono bbox drawn")
    _assert(non_sono_result["data_source_type"] == "generic_vegetation_proxy", "non-sono generic growth")
    checks.append("non_sono_generic_growth")

    missing_conductor = _snapshot_with_mock(
        client,
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [_det("pohon_sono", [250, 165, 520, 455], 0.82, "tree target visible")],
        },
        gps=False,
    )
    missing_result = missing_conductor["result"]
    _assert(missing_result["detection_count"] == 1, "tree-only detection remains")
    _assert(missing_result["conductor_status"] == "tidak tervalidasi", "missing conductor status")
    _assert(missing_result["zone_status"] == "unavailable", "missing conductor zone unavailable")
    _assert(missing_result["prediction_window"] == "data tidak cukup" or missing_result["manual_review_required"] is True, "missing conductor conservative")
    _assert(missing_result["risk_status"] != "ZONA_TEBANG" or missing_result["zone_status"] != "precise", "no precise false zone")
    checks.append("missing_conductor_conservative")

    accepted_before = _line_count(ACCEPTED_JSONL)
    accept = client.post("/api/plan-c/operator-feedback", json={"session_id": ready["session_id"], "verdict": "accepted"})
    _assert(accept.status_code == 200, "accept feedback HTTP")
    _assert(accept.get_json()["status"] == "OPERATOR_ACCEPTED_REFERENCE_SAVED", "accept status")
    _assert(_line_count(ACCEPTED_JSONL) == accepted_before + 1, "accepted jsonl append")
    _assert((ACCEPTED_JSONL.parent / "yolo_compatible_labels" / f"{ready['session_id']}.txt").exists(), "accepted label saved")

    reject_target = _snapshot_with_mock(
        client,
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [
                _det("pohon_sono", [250, 170, 510, 450], 0.88, "pohon sono candidate"),
                _det("konduktor", [70, 120, 580, 145], 0.84, "overhead conductor"),
                _det("struktur_penyangga", [30, 60, 85, 460], 0.81, "utility pole support"),
            ],
        },
        gps=True,
    )
    rejected_before = _line_count(REJECTED_JSONL)
    reject = client.post("/api/plan-c/operator-feedback", json={"session_id": reject_target["session_id"], "verdict": "rejected"})
    _assert(reject.status_code == 200, "reject feedback HTTP")
    _assert(reject.get_json()["status"] == "REJECTED_REMOVED_FROM_ACTIVE_RESULTS", "reject status")
    _assert(_line_count(REJECTED_JSONL) == rejected_before + 1, "rejected jsonl append")
    map_page = client.get("/plan-c/map").get_data(as_text=True)
    _assert(reject_target["session_id"] not in map_page, "rejected hidden from active map")
    checks.append("feedback_accept_reject_map_filter")

    print("PROGRESS_8_3_PLAN_C_DETECTION_ZONE_SMOKE_PASS")
    print(f"checks={','.join(checks)}")
    print(f"ready_session_id={ready['session_id']}")
    print(f"reject_session_id={reject_target['session_id']}")
    return 0


def _snapshot_with_mock(client, *, mock_payload: dict, gps: bool) -> dict:
    session_id = client.post("/api/plan-c/session/start", json={}).get_json()["session_id"]
    payload = {
        "session_id": session_id,
        "idempotency_key": f"{session_id}:{uuid.uuid4()}",
        "image_data": "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes()).decode("ascii"),
        "mock_detection_payload": mock_payload,
    }
    if gps:
        payload.update({"latitude": -7.231, "longitude": 112.735, "gps_accuracy_m": 8.0, "gps_status": "GPS_READY"})
    response = client.post("/api/plan-c/session/snapshot", json=payload)
    _assert(response.status_code in {200, 201, 202}, f"snapshot HTTP {response.status_code}: {response.get_data(as_text=True)}")
    result = client.get(f"/api/plan-c/session/{session_id}/result").get_json()
    _assert(result.get("status") == "PLAN_C_RESULT_READY", "result ready")
    return {"session_id": session_id, "result": result}


def _det(class_name: str, bbox: list[int], confidence: float, reason: str) -> dict:
    return {
        "class_name": class_name,
        "bbox_format": "xyxy",
        "bbox_xyxy": bbox,
        "confidence": confidence,
        "review_status": "REVIEW",
        "reason": reason,
    }


def _jpeg_bytes() -> bytes:
    from PIL import Image

    image = Image.new("RGB", (640, 480), color=(76, 106, 83))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
