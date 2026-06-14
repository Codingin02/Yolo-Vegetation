from __future__ import annotations

import base64
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.plan_c_growth_model import (  # noqa: E402
    load_csv_reference,
    load_excel_reference,
    load_growth_profile,
)
from ulp_project.plan_c_storage import (  # noqa: E402
    PLAN_C_MARKERS_JSON,
    PLAN_C_RECORDS_CSV,
    PLAN_C_RECORDS_JSONL,
    PLAN_C_REFERENCE_DIR,
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

FORBIDDEN_STAGED_PREFIXES = (
    "data/raw/",
    "data/gps/",
    "data/processed/",
    "data/exports/",
    "data/dataset_yolo/",
    "dataset_botol/",
    "results/",
    "runs/",
    "weights/",
    "models/",
    "outputs/",
    "reports/",
    "manual_backups/",
)
FORBIDDEN_STAGED_PARTS = (".env", "token", "credential", "ngrok")
FORBIDDEN_STAGED_SUFFIXES = (
    ".pt",
    ".onnx",
    ".engine",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
)


def main() -> int:
    checks: list[str] = []

    import ulp_project.plan_c_ai_validator  # noqa: F401
    import ulp_project.plan_c_geometry  # noqa: F401
    import ulp_project.plan_c_growth_model  # noqa: F401
    import ulp_project.plan_c_map  # noqa: F401
    import ulp_project.plan_c_processor  # noqa: F401
    import ulp_project.plan_c_routes  # noqa: F401
    import ulp_project.plan_c_session  # noqa: F401
    import ulp_project.plan_c_storage  # noqa: F401
    import ulp_project.plan_c_yolo  # noqa: F401

    checks.append("import_plan_c_modules")
    app = create_app()
    client = app.test_client()
    checks.append("create_app")

    _assert(client.get("/plan-c").status_code == 200, "/plan-c HTTP 200")
    checks.append("GET /plan-c")

    ui_version = client.get("/api/plan-c/runtime/ui-version")
    _assert(ui_version.status_code == 200, "runtime ui-version HTTP 200")
    ui_json = ui_version.get_json()
    _assert(
        ui_json.get("runtime_mode")
        in {"PLAN_C_SYSTEM_C_SINGLE_CLASS_POHON_SONO", "PLAN_C_SINGLE_CLASS_POHON_SONO"},
        "runtime mode single class",
    )
    _assert(ui_json.get("detector") == "YOLOv8", "runtime detector YOLOv8")
    _assert(ui_json.get("ai_core_mode") in {None, "THREE_PROVIDER_CONSENSUS"}, "runtime ai core compatible")
    _assert(ui_json.get("active_class") == "pohon_sono", "active class pohon_sono")
    _assert(ui_json.get("multi_class_runtime") is False, "multi_class_runtime false")
    checks.append("GET /api/plan-c/runtime/ui-version")

    start = client.post("/api/plan-c/session/start", json={})
    _assert(start.status_code == 201, "session start HTTP 201")
    start_json = start.get_json()
    session_id = start_json.get("session_id")
    _assert(isinstance(session_id, str) and session_id.startswith("PC_"), "session_id prefix PC_")
    checks.append("POST /api/plan-c/session/start")

    capture = client.get(f"/plan-c/capture/{session_id}")
    _assert(capture.status_code == 200, "capture HTTP 200")
    capture_text = capture.get_data(as_text=True)
    for forbidden in ["YOLO-FIRST", "vision-analyze", "MODEL_STATUS_UNKNOWN"]:
        _assert(forbidden not in capture_text, f"capture must not contain {forbidden}")
    checks.append("GET /plan-c/capture/<session_id>")

    anchor = client.post(
        "/api/plan-c/session/tree-anchor",
        json={"session_id": session_id, "latitude": -7.231, "longitude": 112.735, "gps_accuracy_m": 8.5},
    )
    _assert(anchor.status_code in {200, 201}, "tree-anchor HTTP 200/201")
    checks.append("POST /api/plan-c/session/tree-anchor")

    csv_before = count_csv_rows(PLAN_C_RECORDS_CSV)
    jsonl_before = count_jsonl_rows(PLAN_C_RECORDS_JSONL)
    marker_before = len(read_markers())

    snapshot = client.post(
        "/api/plan-c/session/snapshot",
        data={
            "session_id": session_id,
            "latitude": "-7.231",
            "longitude": "112.735",
            "gps_accuracy_m": "8.5",
            "snapshot": (BytesIO(_build_test_image_bytes()), "snapshot.jpg"),
        },
        content_type="multipart/form-data",
    )
    _assert(snapshot.status_code in {200, 201, 202}, f"snapshot HTTP {snapshot.status_code}")
    checks.append("POST /api/plan-c/session/snapshot")

    status = client.get(f"/api/plan-c/session/{session_id}/status")
    _assert(status.status_code == 200, "status HTTP 200")
    _assert(status.get_json().get("result_ready") is True, "result ready")
    checks.append("GET /api/plan-c/session/<session_id>/status")

    result_api = client.get(f"/api/plan-c/session/{session_id}/result")
    _assert(result_api.status_code == 200, "result API HTTP 200")
    result_json = result_api.get_json()
    _assert(result_json.get("status") == "PLAN_C_RESULT_READY", "result status ready")
    result_payload_text = json.dumps(result_json, ensure_ascii=False)
    _assert(
        result_json.get("runtime_mode")
        in {"PLAN_C_SYSTEM_C_SINGLE_CLASS_POHON_SONO", "PLAN_C_SINGLE_CLASS_POHON_SONO"},
        "result runtime mode single class",
    )
    _assert(result_json.get("detector") == "YOLOv8", "result detector YOLOv8")
    _assert(result_json.get("yolo_mode") == "single_class", "result yolo mode single_class")
    _assert(result_json.get("ai_core_mode") == "THREE_PROVIDER_CONSENSUS", "result ai core consensus")
    _assert(result_json.get("detected_primary_object") == "pohon_sono", "detected primary object pohon_sono")
    _assert(result_json.get("multi_class_runtime") is False, "result multi_class_runtime false")
    _assert(result_json.get("conductor_required_for_detection") is False, "conductor not required for detection")
    _assert(result_json.get("zone_overlay_status") == "ZONE_OVERLAY_RENDERED", "zone overlay rendered")
    _assert(result_json.get("zone_method"), "zone method present")
    _assert(result_json.get("zone_final"), "zone final present")
    _assert(result_json.get("prediction_window") is not None, "prediction window present")
    _assert(
        result_json.get("risk_status")
        in {
            "ZONA_TEBANG",
            "ZONA_PANTAU",
            "ZONA_AMAN",
            "DATA_TIDAK_CUKUP",
            "POHON_SONO_DETECTED_REVIEW_REQUIRED",
            "ZONA_TEBANG_REVIEW",
            "ZONA_TEBANG_MANUAL_REVIEW",
        },
        f"unexpected risk_status: {result_json.get('risk_status')}",
    )
    _assert("AI detected" not in result_payload_text, "result json must not contain AI detected")
    _assert(
        "DATA_TIDAK_CUKUP_KONDUKTOR_TIDAK_TERVALIDASI" not in result_payload_text,
        "conductor-not-validated hard blocker removed",
    )
    checks.append("GET /api/plan-c/session/<session_id>/result")

    result_page = client.get(f"/plan-c/result/{session_id}")
    _assert(result_page.status_code == 200, "result page HTTP 200")
    result_text = result_page.get_data(as_text=True)
    _assert("risk_status" in result_text and "prediction_window" in result_text, "result page risk/prediction")
    _assert("YOLOv8" in result_text, "result page contains YOLOv8")
    _assert("pohon_sono" in result_text, "result page contains pohon_sono")
    _assert("AI detected" not in result_text, "result page must not contain AI detected")
    _assert("multi-class runtime" not in result_text, "result page must not contain multi-class runtime")
    checks.append("GET /plan-c/result/<session_id>")

    developer = client.get(f"/plan-c/developer/{session_id}")
    _assert(developer.status_code == 200, "developer page HTTP 200")
    _assert("raw diagnostics" in developer.get_data(as_text=True), "developer raw diagnostics")
    checks.append("GET /plan-c/developer/<session_id>")

    map_page = client.get("/plan-c/map")
    _assert(map_page.status_code == 200, "map HTTP 200")
    checks.append("GET /plan-c/map")

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
        path = session_file(session_id, filename)
        _assert(path.exists(), f"{filename} created")
        if filename == "annotated.jpg":
            _assert(path.stat().st_size > 0, "annotated.jpg non-empty")
    checks.append("session_files_created")

    yolo_raw = _read_json(session_file(session_id, "yolo_raw.json"))
    _assert(yolo_raw.get("model_policy") == "single_class_pohon_sono", "yolo_raw model policy single class")
    _assert(yolo_raw.get("multi_class_runtime") is False, "yolo_raw multi_class_runtime false")
    _assert(yolo_raw.get("active_detection_target") == "pohon_sono", "yolo_raw active target pohon_sono")
    if (ROOT / "models" / "plan_c_ai_detector" / "best.pt").exists():
        _assert(
            yolo_raw.get("status")
            in {
                "YOLOV8_SINGLE_CLASS_POHON_SONO_READY",
                "YOLOV8_POHON_SONO_READY",
                "YOLOV8_MODEL_READY_CLASS_MAPPING_REVIEW_REQUIRED",
                "YOLOV8_INFERENCE_FAILED",
            },
            f"unexpected yolo status with model present: {yolo_raw.get('status')}",
        )
    else:
        _assert(yolo_raw.get("status") == "YOLO_MODEL_NOT_READY", "missing model status")
        _assert(yolo_raw.get("detections") == [], "missing model detections empty")
    checks.append("single_class_yolo_raw")

    _assert(count_csv_rows(PLAN_C_RECORDS_CSV) == csv_before + 1, "CSV appended one row")
    _assert(count_jsonl_rows(PLAN_C_RECORDS_JSONL) == jsonl_before + 1, "JSONL appended one line")
    _assert(len(read_markers()) >= marker_before + 1, "marker appended")
    _assert(PLAN_C_MARKERS_JSON.exists(), "marker file exists")
    checks.append("append_only_csv_jsonl_map")

    growth = load_growth_profile(PLAN_C_REFERENCE_DIR)
    if (PLAN_C_REFERENCE_DIR / "plan_c_growth_profile.json").exists():
        _assert(growth.get("json_status") == "GROWTH_PROFILE_LOADED", "JSON growth profile loaded")
    csv_growth = load_csv_reference(PLAN_C_REFERENCE_DIR / "pohon_sono_growth_reference.csv")
    if (PLAN_C_REFERENCE_DIR / "pohon_sono_growth_reference.csv").exists():
        _assert(csv_growth.get("status") == "CSV_REFERENCE_LOADED", "CSV reference loaded")
        _assert(csv_growth.get("row_count", 0) > 0, "CSV leading blank line tolerated")
    excel_growth = load_excel_reference(PLAN_C_REFERENCE_DIR / "pohon_sono_growth_reference.xlsx")
    _assert(
        excel_growth.get("status") in {
            "EXCEL_REFERENCE_LOADED",
            "EXCEL_REFERENCE_MISSING",
            "EXCEL_REFERENCE_SKIPPED_OPENPYXL_NOT_AVAILABLE",
        },
        "Excel loader fallback did not fail",
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        missing = load_growth_profile(Path(temp_dir))
        _assert(missing.get("growth_profile_status") == "GROWTH_PROFILE_MISSING", "missing growth profile safe")
        _assert(missing.get("prediction_window") == "data tidak cukup", "missing growth profile data not enough")
    checks.append("growth_loaders")

    diff_check = subprocess.run(["cmd", "/c", "git diff --check"], cwd=ROOT, text=True, capture_output=True)
    _assert(diff_check.returncode == 0, f"git diff --check failed: {diff_check.stdout}{diff_check.stderr}")
    checks.append("git diff --check")

    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True, check=True)
    forbidden = [path for path in staged.stdout.splitlines() if _is_forbidden_staged(path.replace("\\", "/"))]
    _assert(not forbidden, f"forbidden staged path: {forbidden}")
    checks.append("forbidden_path_not_staged")

    print("PLAN_C_SINGLE_CLASS_POHON_SONO_SMOKE_PASS")
    print(f"session_id={session_id}")
    print(f"csv_path={PLAN_C_RECORDS_CSV}")
    print(f"jsonl_path={PLAN_C_RECORDS_JSONL}")
    print(f"markers_path={PLAN_C_MARKERS_JSON}")
    print(f"checks={','.join(checks)}")
    print(f"growth_json_status={growth.get('json_status')}")
    print(f"growth_csv_status={growth.get('csv_status')}")
    print(f"growth_excel_status={growth.get('excel_status')}")
    print(f"yolo_status={result_json.get('yolo_status')}")
    print(f"ai_validator_status={result_json.get('ai_validator_status')}")
    print(f"ai_core_mode={result_json.get('ai_core_mode')}")
    print(f"final_detection_source={result_json.get('final_detection_source')}")
    print(f"zone_overlay_status={result_json.get('zone_overlay_status')}")
    print(f"risk_status={result_json.get('risk_status')}")
    print(f"annotated_image_path={session_file(session_id, 'annotated.jpg')}")
    print(f"geometry_status={result_json.get('geometry_status')}")
    return 0


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_test_image_bytes() -> bytes:
    try:
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (640, 900), (190, 210, 230))
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, 640, 300], fill=(170, 190, 210))
        draw.rectangle([0, 300, 640, 610], fill=(184, 176, 130))
        draw.rectangle([0, 610, 640, 900], fill=(92, 128, 76))
        draw.rectangle([302, 360, 338, 820], fill=(96, 62, 38))
        draw.ellipse([150, 130, 500, 560], fill=(32, 132, 64))
        draw.ellipse([210, 80, 450, 360], fill=(38, 150, 73))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()
    except Exception:
        return JPEG_BYTES


def _is_forbidden_staged(path: str) -> bool:
    lowered = path.lower()
    return (
        lowered.startswith(FORBIDDEN_STAGED_PREFIXES)
        or any(part in lowered for part in FORBIDDEN_STAGED_PARTS)
        or lowered.endswith(FORBIDDEN_STAGED_SUFFIXES)
    )


if __name__ == "__main__":
    raise SystemExit(main())
