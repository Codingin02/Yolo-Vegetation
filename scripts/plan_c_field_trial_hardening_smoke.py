from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.plan_c_growth_model import load_csv_reference, load_growth_profile  # noqa: E402
from ulp_project.plan_c_storage import (  # noqa: E402
    PLAN_C_RECORDS_CSV,
    PLAN_C_RECORDS_JSONL,
    count_csv_rows,
    count_jsonl_rows,
    read_markers,
    session_file,
)

SECRET_MARKERS = [
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "NGROK_AUTHTOKEN",
    "SERVICE_ACCOUNT",
    "credential",
    "token",
]
LONG_BASE64_RE = re.compile(r"[A-Za-z0-9+/=]{240,}")


def main() -> int:
    app = create_app()
    client = app.test_client()
    checks: list[str] = ["create_app"]

    _assert(client.get("/plan-c").status_code == 200, "GET /plan-c")
    checks.append("GET /plan-c")

    start = client.post("/api/plan-c/session/start", json={"operator_name": "smoke"})
    _assert(start.status_code == 201, "session start HTTP 201")
    session_id = start.get_json().get("session_id")
    _assert(isinstance(session_id, str) and session_id.startswith("PC_"), "session_id")
    checks.append("POST /api/plan-c/session/start")

    anchor = client.post(
        "/api/plan-c/session/tree-anchor",
        json={"session_id": session_id, "latitude": -7.231, "longitude": 112.735, "gps_accuracy_m": 9.0},
    )
    _assert(anchor.status_code in {200, 201}, "tree anchor status code")
    _assert(anchor.get_json().get("status") in {"TREE_ANCHOR_SAVED", "TREE_ANCHOR_ACCEPTED_DEGRADED"}, "tree anchor status")
    checks.append("POST /api/plan-c/session/tree-anchor")

    csv_before = count_csv_rows(PLAN_C_RECORDS_CSV)
    jsonl_before = count_jsonl_rows(PLAN_C_RECORDS_JSONL)
    marker_before = len(read_markers())
    idempotency_key = f"{session_id}:{uuid.uuid4()}"
    data_url = "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes()).decode("ascii")

    first = client.post(
        "/api/plan-c/session/snapshot",
        json={
            "session_id": session_id,
            "idempotency_key": idempotency_key,
            "point_id": "pohon_sono",
            "image_data": data_url,
            "latitude": -7.231,
            "longitude": 112.735,
            "gps_accuracy_m": 9.0,
            "gps_status": "GPS_READY",
        },
    )
    _assert(first.status_code in {200, 201, 202}, f"snapshot first HTTP {first.status_code}")
    first_json = first.get_json()
    _assert(first_json.get("status") == "PLAN_C_RESULT_READY", "snapshot first ready")
    checks.append("POST /api/plan-c/session/snapshot first")

    duplicate = client.post(
        "/api/plan-c/session/snapshot",
        json={
            "session_id": session_id,
            "idempotency_key": idempotency_key,
            "image_data": data_url,
            "latitude": -7.231,
            "longitude": 112.735,
            "gps_accuracy_m": 9.0,
            "gps_status": "GPS_READY",
        },
    )
    _assert(duplicate.status_code in {200, 202}, "duplicate HTTP controlled")
    duplicate_json = duplicate.get_json()
    _assert(duplicate_json.get("status") in {"PLAN_C_SNAPSHOT_ALREADY_PROCESSED", "PLAN_C_SNAPSHOT_PROCESSING"}, "duplicate status")
    _assert(duplicate_json.get("duplicate_ignored") is True, "duplicate ignored")
    _assert(count_csv_rows(PLAN_C_RECORDS_CSV) == csv_before + 1, "duplicate did not append CSV")
    _assert(count_jsonl_rows(PLAN_C_RECORDS_JSONL) == jsonl_before + 1, "duplicate did not append JSONL")
    _assert(len(read_markers()) == marker_before + 1, "duplicate did not append marker")
    checks.append("idempotency duplicate guard")

    status = client.get(f"/api/plan-c/session/{session_id}/status")
    _assert(status.status_code == 200 and status.is_json, "status JSON")
    result_api = client.get(f"/api/plan-c/session/{session_id}/result")
    _assert(result_api.status_code == 200 and result_api.is_json, "result API JSON")
    result_json = result_api.get_json()
    _assert(result_json.get("status") == "PLAN_C_RESULT_READY", "result JSON ready")
    checks.append("status/result API")

    result_page = client.get(f"/plan-c/result/{session_id}")
    _assert(result_page.status_code == 200, "result page 200")
    developer_page = client.get(f"/plan-c/developer/{session_id}")
    _assert(developer_page.status_code == 200, "developer page 200")
    map_page = client.get("/plan-c/map")
    _assert(map_page.status_code == 200, "map page 200")
    ui_version = client.get("/api/plan-c/runtime/ui-version")
    _assert(ui_version.status_code == 200, "ui version 200")
    _assert(ui_version.get_json().get("plan_c_ui_version") == "progress8_1_plan_c_field_trial_hardening", "ui version value")
    checks.append("pages/ui-version")

    for filename in [
        "original.jpg",
        "annotated.jpg",
        "result.json",
        "developer.json",
        "metadata.json",
        "yolo_raw.json",
        "ai_raw.json",
        "geometry.json",
    ]:
        _assert(session_file(session_id, filename).exists(), f"{filename} exists")
    checks.append("session files")

    no_gps_start = client.post("/api/plan-c/session/start", json={})
    no_gps_session_id = no_gps_start.get_json().get("session_id")
    marker_before_no_gps = len(read_markers())
    raw_base64 = base64.b64encode(_jpeg_bytes()).decode("ascii")
    no_gps = client.post(
        "/api/plan-c/session/snapshot",
        json={
            "session_id": no_gps_session_id,
            "idempotency_key": f"{no_gps_session_id}:{uuid.uuid4()}",
            "image_data": raw_base64,
            "gps_status": "GPS_PERMISSION_DENIED",
        },
    )
    _assert(no_gps.status_code in {200, 201, 202}, "raw base64 no GPS snapshot controlled")
    _assert(len(read_markers()) == marker_before_no_gps, "no GPS did not append marker")
    checks.append("raw_base64_no_fake_gps")

    with tempfile.TemporaryDirectory() as temp_dir:
        missing = load_growth_profile(Path(temp_dir))
        _assert(missing.get("prediction_window") == "data tidak cukup", "missing growth no crash")
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "blank_first_line.csv"
        csv_path.write_text("\nvalue\n0.1\n", encoding="utf-8")
        csv_result = load_csv_reference(csv_path)
        _assert(csv_result.get("status") == "CSV_REFERENCE_LOADED", "blank first line CSV loaded")
        _assert(csv_result.get("row_count") == 1, "blank first line row count")
    checks.append("growth fallback/csv blank")

    developer_text = developer_page.get_data(as_text=True)
    for marker in SECRET_MARKERS:
        _assert(marker not in developer_text, f"developer redaction marker {marker}")
    _assert("data:image" not in developer_text, "developer no data URL")
    _assert(not LONG_BASE64_RE.search(developer_text), "developer no long base64")
    checks.append("developer redaction")

    diff_check = subprocess.run(["cmd", "/c", "git diff --check"], cwd=ROOT, text=True, capture_output=True)
    _assert(diff_check.returncode == 0, f"git diff --check failed: {diff_check.stdout}{diff_check.stderr}")
    checks.append("git diff --check")

    print("PROGRESS_8_1_PLAN_C_FIELD_TRIAL_HARDENING_SMOKE_PASS")
    print(f"session_id={session_id}")
    print(f"duplicate_status={duplicate_json.get('status')}")
    print(f"growth_status={result_json.get('growth_profile_status')}")
    print(f"yolo_status={result_json.get('yolo_status')}")
    print(f"ai_validator_status={result_json.get('ai_validator_status')}")
    print(f"geometry_status={result_json.get('geometry_status')}")
    print(f"checks={','.join(checks)}")
    return 0


def _jpeg_bytes() -> bytes:
    try:
        from PIL import Image

        image = Image.new("RGB", (32, 24), color=(40, 90, 64))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()
    except Exception:
        return base64.b64decode(
            "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
            "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QA"
            "FQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oA"
            "CAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/Aaf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/Aaf/xAAU"
            "EAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Aqf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/E"
            "ABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAAAAA"
            "AAAAAAAAABD/2gAIAQEAAT8QH//Z"
        )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
