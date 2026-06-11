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

    precise = _snapshot_with_mock(
        client,
        image_size=(1000, 1600),
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [
                _det("konduktor", [100, 345, 900, 355], 0.9, "tight overhead distribution conductor"),
                _det("struktur_penyangga", [40, 100, 90, 540], 0.88, "utility pole support"),
                _det("pohon_sono", [360, 430, 700, 1300], 0.86, "pohon sono candidate with visible base"),
            ],
        },
        gps=True,
    )
    result = precise["result"]
    _assert(result["zone_status"] == "precise", "precise zone status")
    _assert(_near(result["zone_tebang_y1"], 350), "zone tebang y1")
    _assert(_near(result["zone_tebang_y2"], 470), "zone tebang y2")
    _assert(_near(result["zone_pantau_y1"], 470), "zone pantau y1")
    _assert(_near(result["zone_pantau_y2"], 590), "zone pantau y2")
    _assert(_near(result["zone_aman_y1"], 590), "zone aman y1")
    _assert(_near(result["zone_aman_y2"], 1300), "zone aman y2")
    _assert(result["risk_status"] in {"AMAN", "PANTAU", "ZONA_TEBANG"}, "precise risk useful")
    _assert(result["prediction_window"] != "data tidak cukup", "precise prediction useful")
    labels = [item.get("label") for item in result.get("zone_summary", {}).get("zones", [])]
    _assert("ZONA TEBANG 0-3 m di bawah konduktor" in labels, "zone tebang label")
    _assert("ZONA PANTAU" in labels, "zone pantau label")
    _assert("ZONA AMAN" in labels, "zone aman label")
    _assert(session_file(precise["session_id"], "annotated.jpg").exists(), "precise annotated exists")
    checks.append("precise_zone_geometry")

    no_conductor = _snapshot_with_mock(
        client,
        image_size=(1000, 1600),
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [_det("pohon_sono", [360, 430, 700, 1300], 0.86, "pohon sono candidate")],
        },
        gps=False,
    )
    no_conductor_result = no_conductor["result"]
    _assert(no_conductor_result["zone_status"] == "unavailable", "missing conductor unavailable")
    _assert(no_conductor_result["risk_status"] == "DATA_TIDAK_CUKUP", "missing conductor data not enough")
    _assert(no_conductor_result.get("zone_summary", {}).get("zones") == [], "missing conductor no precise zones")
    _assert("KONDUKTOR TIDAK TERVALIDASI" in no_conductor_result.get("zone_summary", {}).get("message", ""), "missing conductor message")
    checks.append("conductor_not_validated")

    non_sono = _snapshot_with_mock(
        client,
        image_size=(1000, 1600),
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [
                _det("tree", [360, 430, 700, 1300], 0.82, "clear tree but species not confirmed"),
                _det("konduktor", [100, 345, 900, 355], 0.86, "tight overhead conductor"),
                _det("struktur_penyangga", [40, 100, 90, 540], 0.84, "utility pole support"),
            ],
        },
        gps=False,
    )
    non_sono_result = non_sono["result"]
    _assert(non_sono_result["tree_species_status"] == "pohon_non_sono", "non-sono tree status")
    _assert(any(item["class_name"] == "pohon_non_sono" for item in non_sono_result["detections"]), "non-sono bbox kept")
    _assert(non_sono_result["data_source_type"] == "generic_vegetation_proxy", "non-sono generic growth")
    checks.append("non_sono_generic_growth")

    indoor = _snapshot_with_mock(
        client,
        image_size=(1000, 1600),
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [
                _det("person", [240, 320, 600, 1240], 0.92, "person head chin body indoor"),
                _det("head", [310, 340, 520, 560], 0.9, "head and face"),
                _det("wall", [0, 0, 1000, 1600], 0.8, "wall background"),
            ],
            "negative_findings": [{"object": "person", "action": "ignored", "reason": "not a target object"}],
        },
        gps=False,
    )
    indoor_result = indoor["result"]
    _assert(indoor_result["detection_count"] == 0, "indoor false positives rejected")
    _assert(indoor_result["conductor_status"] == "tidak tervalidasi", "indoor no conductor")
    _assert(indoor_result["risk_status"] == "DATA_TIDAK_CUKUP", "indoor data not enough")
    checks.append("false_positive_person_indoor")

    multi = _snapshot_with_mock(
        client,
        image_size=(1000, 1600),
        mock_payload={
            "status": "DETECTION_READY",
            "image_quality": "clear",
            "detections": [
                _det("konduktor", [100, 326, 900, 334], 0.86, "first overhead conductor line"),
                _det("konduktor", [100, 346, 900, 354], 0.87, "second overhead conductor line"),
                _det("konduktor", [100, 366, 900, 374], 0.88, "third overhead conductor line"),
                _det("struktur_penyangga", [40, 100, 90, 540], 0.84, "utility pole support"),
                _det("pohon_sono", [360, 430, 700, 1300], 0.84, "pohon sono candidate"),
            ],
        },
        gps=False,
    )
    multi_result = multi["result"]
    _assert(int(multi_result.get("conductor_group_count") or 0) >= 3, "multiple conductor group count")
    _assert(len(multi_result.get("conductor_lines") or []) >= 3, "multiple conductor lines")
    _assert(_near(multi_result.get("conductor_y"), 370), "multiple conductor conservative reference")
    checks.append("multiple_conductors")

    capture_template = (ROOT / "src" / "ulp_project" / "templates" / "plan_c_capture.html").read_text(encoding="utf-8")
    _assert("plan_c_fullscreen_camera_v4.css" in capture_template, "capture v4 css")
    _assert("plan_c_fullscreen_camera_v4.js" in capture_template, "capture v4 js")
    _assert("plan_c_bottom_nav_v4" in capture_template, "bottom nav v4 asset")
    _assert("plan_c_capture.js" not in capture_template, "old capture js absent")
    forbidden_capture = ["cameraStatus", "gpsStatus", "serverStatus", "manualDistance", "manualClearance", "manualTreeHeight"]
    _assert(not any(token in capture_template for token in forbidden_capture), "old operator chips absent")
    checks.append("capture_ui_v4_assets")

    accepted_before = _line_count(ACCEPTED_JSONL)
    accept = client.post("/api/plan-c/operator-feedback", json={"session_id": precise["session_id"], "verdict": "accepted"})
    _assert(accept.status_code == 200, "accept feedback HTTP")
    _assert(accept.get_json()["status"] == "OPERATOR_ACCEPTED_REFERENCE_SAVED", "accept feedback status")
    _assert(_line_count(ACCEPTED_JSONL) == accepted_before + 1, "accept jsonl append")

    rejected_before = _line_count(REJECTED_JSONL)
    reject = client.post("/api/plan-c/operator-feedback", json={"session_id": multi["session_id"], "verdict": "rejected"})
    _assert(reject.status_code == 200, "reject feedback HTTP")
    _assert(reject.get_json()["status"] == "REJECTED_REMOVED_FROM_ACTIVE_RESULTS", "reject feedback status")
    _assert(_line_count(REJECTED_JSONL) == rejected_before + 1, "reject jsonl append")
    _assert(session_file(multi["session_id"], "original.jpg").exists(), "reject does not delete original")
    map_page = client.get("/plan-c/map").get_data(as_text=True)
    _assert(multi["session_id"] not in map_page, "rejected hidden from active map")
    checks.append("feedback_learning_gate")

    print("PROGRESS_8_4_PLAN_C_FINAL_ZONE_GEOMETRY_SMOKE_PASS")
    print(f"checks={','.join(checks)}")
    print(f"precise_session_id={precise['session_id']}")
    return 0


def _snapshot_with_mock(client, *, image_size: tuple[int, int], mock_payload: dict, gps: bool) -> dict:
    session_id = client.post("/api/plan-c/session/start", json={}).get_json()["session_id"]
    payload = {
        "session_id": session_id,
        "idempotency_key": f"{session_id}:{uuid.uuid4()}",
        "image_data": "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes(image_size)).decode("ascii"),
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


def _jpeg_bytes(size: tuple[int, int]) -> bytes:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", size, color=(68, 95, 72))
    draw = ImageDraw.Draw(image)
    draw.line([100, 350, size[0] - 100, 350], fill=(35, 35, 35), width=5)
    draw.rectangle([40, 100, 90, 540], fill=(105, 105, 110))
    draw.rectangle([360, 430, 700, 1300], fill=(26, 120, 62))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())


def _near(value: object, expected: float, tolerance: float = 1.0) -> bool:
    try:
        return abs(float(value) - float(expected)) <= tolerance
    except (TypeError, ValueError):
        return False


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
