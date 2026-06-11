from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.plan_c_ai_model_runtime import get_plan_c_ai_model_status  # noqa: E402
from ulp_project.plan_c_storage import (  # noqa: E402
    PLAN_C_RECORDS_CSV,
    PLAN_C_RECORDS_JSONL,
    count_csv_rows,
    count_jsonl_rows,
    read_markers,
    session_file,
)

JPEG_BYTES = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QA"
    "FQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oA"
    "CAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/Aaf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/Aaf/xAAU"
    "EAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Aqf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/E"
    "ABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAAAAA"
    "AAAAAAAAABD/2gAIAQEAAT8QH//Z"
)


def make_valid_jpeg_bytes() -> bytes:
    try:
        from PIL import Image

        buffer = BytesIO()
        image = Image.new("RGB", (96, 96), color=(72, 132, 80))
        image.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()
    except Exception:
        return JPEG_BYTES


def main() -> int:
    app = create_app()
    client = app.test_client()

    upload_page = client.get("/plan-c/upload")
    _assert(upload_page.status_code == 200, "GET /plan-c/upload")
    upload_text = upload_page.get_data(as_text=True)
    _assert("type=\"file\"" in upload_text and "accept=\"image/*\"" in upload_text, "file picker exists")
    _assert("sementara" not in upload_text.lower(), "operator upload page wording")

    legacy = client.get("/plan-c")
    _assert(legacy.status_code == 200, "legacy /plan-c remains available")

    csv_before = count_csv_rows(PLAN_C_RECORDS_CSV)
    jsonl_before = count_jsonl_rows(PLAN_C_RECORDS_JSONL)
    markers_before = len(read_markers())

    start = client.post(
        "/api/plan-c/upload/start",
        data={
            "image": (BytesIO(make_valid_jpeg_bytes()), "upload.jpg"),
            "latitude": "-7.231",
            "longitude": "112.735",
            "accuracy_m": "6.5",
            "operator_name": "smoke",
            "point_id": "SMOKE_UPLOAD",
            "notes": "upload smoke",
            "source_mode": "UPLOAD_IMAGE_MODE",
        },
        content_type="multipart/form-data",
    )
    _assert(start.status_code == 201, f"upload start status {start.status_code}")
    start_json = start.get_json()
    session_id = start_json.get("session_id")
    _assert(isinstance(session_id, str) and session_id.startswith("PC_UPLOAD_"), "upload session id")
    _assert(start_json.get("status") == "UPLOAD_ACCEPTED_DETECTION_PENDING", "initial status")
    _assert(session_file(session_id, "metadata.json").exists(), "metadata created")
    _assert(session_file(session_id, "original.jpg").exists(), "original created")

    review = client.get(f"/plan-c/upload/review/{session_id}")
    _assert(review.status_code == 200, "review page 200")
    _assert("Jalankan Deteksi dan Prediksi" in review.get_data(as_text=True), "manual process button")

    process = client.post(f"/api/plan-c/upload/process/{session_id}")
    _assert(process.status_code == 200, f"process status {process.status_code}")
    process_json = process.get_json()
    _assert(process_json.get("status") == "PLAN_C_UPLOAD_RESULT_READY", "process ready")
    result = process_json.get("result") or {}
    model_status = get_plan_c_ai_model_status()
    if model_status.get("model_exists") and model_status.get("registry_exists"):
        _assert(result.get("model_status") == "PLAN_C_AI_MODEL_READY", "model ready status")
    _assert(session_file(session_id, "result.json").exists(), "result created")
    _assert(session_file(session_id, "developer.json").exists(), "developer created")
    _assert(session_file(session_id, "annotated.jpg").exists(), "annotated created")
    _assert(session_file(session_id, "ai_model_raw.json").exists(), "ai model raw created")
    _assert(session_file(session_id, "ai_raw.json").exists(), "ai raw created")
    _assert(session_file(session_id, "geometry.json").exists(), "geometry created")
    _assert(session_file(session_id, "growth.json").exists(), "growth created")
    _assert(result.get("clearance_m") is None or isinstance(result.get("clearance_m"), (int, float)), "clearance null or number")
    if result.get("risk_status") == "DATA_TIDAK_CUKUP":
        _assert(result.get("clearance_m") is None, "data not enough must not create false zero clearance")

    _assert(count_csv_rows(PLAN_C_RECORDS_CSV) == csv_before + 1, "CSV append one")
    _assert(count_jsonl_rows(PLAN_C_RECORDS_JSONL) == jsonl_before + 1, "JSONL append one")
    _assert(len(read_markers()) == markers_before + 1, "GPS marker appended")

    result_api = client.get(f"/api/plan-c/upload/result/{session_id}")
    _assert(result_api.status_code == 200 and result_api.get_json().get("result_ready"), "result API ready")

    result_page = client.get(f"/plan-c/upload/result/{session_id}")
    _assert(result_page.status_code == 200, "result page 200")
    result_text = result_page.get_data(as_text=True)
    _assert("Ultralytics YOLO object detection" not in result_text, "internal engine hidden from operator")
    _assert("sementara" not in result_text.lower(), "result page wording")
    _assert("fake" not in result_text.lower(), "no fake wording")

    developer = client.get(f"/plan-c/upload/developer/{session_id}")
    _assert(developer.status_code == 200, "developer page 200")
    developer_text = developer.get_data(as_text=True)
    _assert("Ultralytics YOLO object detection" in developer_text, "internal engine developer only")
    for forbidden in ["OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "token", "credential"]:
        _assert(forbidden not in developer_text, f"secret redaction {forbidden}")

    diff_check = subprocess.run(["cmd", "/c", "git diff --check"], cwd=ROOT, text=True, capture_output=True)
    _assert(diff_check.returncode == 0, f"git diff --check failed: {diff_check.stdout}{diff_check.stderr}")

    print("PLAN_C_UPLOAD_SMOKE_PASS")
    print(f"session_id={session_id}")
    print(f"model_status={result.get('model_status')}")
    print(f"detection_status={result.get('detection_status')}")
    print(f"risk_status={result.get('risk_status')}")
    print(f"csv_path={PLAN_C_RECORDS_CSV}")
    print(f"jsonl_path={PLAN_C_RECORDS_JSONL}")
    return 0


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
