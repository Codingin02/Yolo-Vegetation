from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.plan_c_free_vision_detector import (  # noqa: E402
    build_free_vision_status_payload,
    detect_yolo_compatible_from_snapshot,
)
from ulp_project.plan_c_free_vision_schema import normalize_detection_payload  # noqa: E402
from ulp_project.plan_c_storage import (  # noqa: E402
    PLAN_C_RECORDS_CSV,
    PLAN_C_RECORDS_JSONL,
    count_csv_rows,
    count_jsonl_rows,
    read_markers,
    session_file,
)
from ulp_project.plan_c_yolo_compatible_renderer import render_yolo_compatible_annotation  # noqa: E402

FORBIDDEN_OPERATOR_WORDS = ["AI", "Gemini", "Groq", "OpenRouter", "LLM", "provider", "API key"]
FORBIDDEN_DEVELOPER_WORDS = [
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "token",
    "credential",
]
LONG_BASE64_RE = re.compile(r"[A-Za-z0-9+/=]{240,}")


def main() -> int:
    _force_no_provider_keys()
    checks: list[str] = []

    app = create_app()
    client = app.test_client()
    checks.append("create_app")

    home = client.get("/plan-c")
    _assert(home.status_code == 200, "GET /plan-c")
    checks.append("GET /plan-c")

    status = client.get("/api/plan-c/free-vision/status")
    _assert(status.status_code == 200, "free vision status HTTP 200")
    status_json = status.get_json()
    _assert(status_json.get("status") == "PLAN_C_FREE_VISION_STATUS_READY", "free vision status payload")
    _assert(all(not item.get("configured") for item in status_json.get("providers", {}).values()), "providers disabled without keys")
    checks.append("GET /api/plan-c/free-vision/status")

    no_key_status = build_free_vision_status_payload(_no_key_config())
    _assert(all(not item.get("configured") for item in no_key_status.get("providers", {}).values()), "no-key config disabled")
    checks.append("no_key_fallback")

    mock = normalize_detection_payload(
        {
            "detections": [
                {"class_name": "tree", "bbox": [100, 120, 450, 800], "bbox_format": "normalized_1000", "confidence": 0.72},
                {"class_name": "wire", "bbox": [20, 330, 980, 360], "bbox_format": "normalized_1000", "confidence": 0.64},
            ]
        },
        image_width=640,
        image_height=480,
    )
    _assert(mock.get("status") == "YOLO_COMPATIBLE_DETECTION_READY", "mock bbox normalized")
    _assert(mock.get("detection_count") == 2, "mock detection count")
    checks.append("mock_provider_bbox")

    temp_original = ROOT / "data" / "runtime" / "plan_c" / "free_vision_smoke_original.jpg"
    temp_annotated = ROOT / "data" / "runtime" / "plan_c" / "free_vision_smoke_annotated.jpg"
    temp_original.parent.mkdir(parents=True, exist_ok=True)
    temp_original.write_bytes(_jpeg_bytes(96, 72))
    render = render_yolo_compatible_annotation(temp_original, temp_annotated, mock["detections"])
    _assert(temp_annotated.exists(), "renderer created annotated image")
    _assert(render.get("detection_count") == 2, "renderer detection count")
    empty_render_path = ROOT / "data" / "runtime" / "plan_c" / "free_vision_smoke_empty.jpg"
    empty_render = render_yolo_compatible_annotation(temp_original, empty_render_path, [])
    _assert(empty_render_path.exists(), "empty detection renderer fallback")
    _assert(empty_render.get("detection_count") == 0, "empty render count")
    checks.append("renderer")

    empty_detection = detect_yolo_compatible_from_snapshot(
        temp_original,
        image_width=96,
        image_height=72,
        config=_no_key_config(),
        yolo_result={"status": "YOLO_MODEL_NOT_READY", "detections": []},
    )
    _assert(empty_detection.get("pipeline_status") == "FREE_VISION_ALL_DISABLED", "all disabled status")
    _assert(empty_detection.get("status") == "DATA_TIDAK_CUKUP", "empty detection data not enough")
    _assert(empty_detection.get("detections") == [], "no fake detection")
    checks.append("empty_detection_no_fake")

    start = client.post("/api/plan-c/session/start", json={})
    _assert(start.status_code == 201, "session start")
    session_id = start.get_json()["session_id"]
    csv_before = count_csv_rows(PLAN_C_RECORDS_CSV)
    jsonl_before = count_jsonl_rows(PLAN_C_RECORDS_JSONL)
    marker_before = len(read_markers())
    key = f"{session_id}:{uuid.uuid4()}"
    snapshot = client.post(
        "/api/plan-c/session/snapshot",
        json={
            "session_id": session_id,
            "idempotency_key": key,
            "image_data": "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes()).decode("ascii"),
            "gps_status": "GPS_PERMISSION_DENIED",
        },
    )
    _assert(snapshot.status_code in {200, 201, 202}, f"snapshot HTTP {snapshot.status_code}")
    _assert(count_csv_rows(PLAN_C_RECORDS_CSV) == csv_before + 1, "CSV append-only")
    _assert(count_jsonl_rows(PLAN_C_RECORDS_JSONL) == jsonl_before + 1, "JSONL append-only")
    _assert(len(read_markers()) == marker_before, "invalid GPS did not append marker")
    _assert(session_file(session_id, "annotated.jpg").exists(), "session annotated exists")
    checks.append("snapshot_append_no_fake_gps")

    result_page = client.get(f"/plan-c/result/{session_id}")
    _assert(result_page.status_code == 200, "result page 200")
    result_text = result_page.get_data(as_text=True)
    for word in FORBIDDEN_OPERATOR_WORDS:
        _assert(not _contains_forbidden_word(result_text, word), f"operator result contains {word}")
    checks.append("operator_ui_redaction")

    developer_page = client.get(f"/plan-c/developer/{session_id}")
    _assert(developer_page.status_code == 200, "developer page 200")
    developer_text = developer_page.get_data(as_text=True)
    for word in FORBIDDEN_DEVELOPER_WORDS:
        _assert(word not in developer_text, f"developer contains {word}")
    _assert("data:image" not in developer_text, "developer no image data URL")
    _assert(not LONG_BASE64_RE.search(developer_text), "developer no long base64")
    checks.append("developer_redaction")

    diff_check = subprocess.run(["cmd", "/c", "git diff --check"], cwd=ROOT, text=True, capture_output=True)
    _assert(diff_check.returncode == 0, f"git diff --check failed: {diff_check.stdout}{diff_check.stderr}")
    checks.append("git diff --check")

    print("PROGRESS_8_2_PLAN_C_FREE_VISION_YOLO_COMPATIBLE_SMOKE_PASS")
    print(f"session_id={session_id}")
    print(f"checks={','.join(checks)}")
    print(f"free_vision_status={status_json.get('status')}")
    print(f"no_key_status=FREE_VISION_ALL_DISABLED")
    print(f"mock_detection_count={mock.get('detection_count')}")
    print(f"renderer_status={render.get('status')}")
    return 0


def _force_no_provider_keys() -> None:
    import os

    os.environ["PLAN_C_VISION_MODE"] = "free_only"
    os.environ["PLAN_C_OPERATOR_HIDE_PROVIDER"] = "true"
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["GROQ_API_KEY"] = ""
    os.environ["OPENROUTER_API_KEY"] = ""
    os.environ["OPENROUTER_VISION_MODEL"] = ""


def _no_key_config() -> dict:
    providers = {
        "primary": {"role": "primary", "name": "gemini", "model": "gemini-2.5-flash", "api_key": "", "configured": False, "status": "FREE_VISION_KEY_MISSING", "free_only": True},
        "secondary": {"role": "secondary", "name": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct", "api_key": "", "configured": False, "status": "FREE_VISION_KEY_MISSING", "free_only": True},
        "tertiary": {"role": "tertiary", "name": "openrouter", "model": "", "api_key": "", "configured": False, "status": "FREE_VISION_KEY_MISSING", "free_only": True},
    }
    return {
        "status": "PLAN_C_FREE_VISION_CONFIG_READY",
        "mode": "free_only",
        "free_only": True,
        "operator_hide_provider": True,
        "provider_order": ["primary", "secondary", "tertiary"],
        "providers": providers,
        "openrouter_free_only": True,
    }


def _jpeg_bytes(width: int = 32, height: int = 24) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (width, height), color=(40, 90, 64))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _contains_forbidden_word(text: str, word: str) -> bool:
    if word == "provider":
        return re.search(r"\bprovider\b", text, flags=re.IGNORECASE) is not None
    if word == "API key":
        return re.search(r"\bAPI key\b", text, flags=re.IGNORECASE) is not None
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
