from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.plan_c_ai_core_consensus import load_provider_config  # noqa: E402
from ulp_project.plan_c_storage import (  # noqa: E402
    PLAN_C_RECORDS_CSV,
    PLAN_C_RECORDS_JSONL,
    count_csv_rows,
    count_jsonl_rows,
    session_file,
)

ALLOWED_RISKS = {
    "ZONA_TEBANG",
    "ZONA_PANTAU",
    "ZONA_AMAN",
    "DATA_TIDAK_CUKUP",
    "POHON_SONO_DETECTED_REVIEW_REQUIRED",
    "ZONA_TEBANG_REVIEW",
    "ZONA_TEBANG_MANUAL_REVIEW",
}


def main() -> int:
    import ulp_project.plan_c_ai_core_consensus as consensus  # noqa: F401

    _load_local_secrets_env()
    provider_config = load_provider_config()
    provider_keys = {
        "Gemini": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "Groq": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "OpenRouter": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
    }

    app = create_app()
    client = app.test_client()
    _assert(client.get("/plan-c").status_code == 200, "/plan-c HTTP 200")

    csv_before = count_csv_rows(PLAN_C_RECORDS_CSV)
    jsonl_before = count_jsonl_rows(PLAN_C_RECORDS_JSONL)

    start = client.post("/api/plan-c/session/start", json={"operator_name": "backend_smoke"})
    _assert(start.status_code == 201, f"session start HTTP {start.status_code}")
    session_id = start.get_json().get("session_id")
    _assert(isinstance(session_id, str) and session_id.startswith("PC_"), "session_id created")

    snapshot = client.post(
        "/api/plan-c/session/snapshot",
        data={
            "session_id": session_id,
            "latitude": "-7.2310",
            "longitude": "112.7350",
            "gps_accuracy_m": "7.0",
            "snapshot": (BytesIO(_build_tree_image_bytes()), "plan_c_backend_smoke.jpg"),
        },
        content_type="multipart/form-data",
    )
    _assert(snapshot.status_code in {200, 201, 202}, f"snapshot HTTP {snapshot.status_code}: {snapshot.get_data(as_text=True)[:500]}")

    result_api = client.get(f"/api/plan-c/session/{session_id}/result")
    _assert(result_api.status_code == 200, f"result API HTTP {result_api.status_code}")
    result_json = result_api.get_json()
    _assert(result_json.get("result_ready") is True, "result ready")

    required_files = ["annotated.jpg", "result.json", "developer.json", "yolo_raw.json", "ai_raw.json", "geometry.json"]
    for filename in required_files:
        path = session_file(session_id, filename)
        _assert(path.exists(), f"{filename} exists")
        _assert(path.stat().st_size > 0, f"{filename} non-empty")

    annotated_path = session_file(session_id, "annotated.jpg")
    ai_raw = _read_json(session_file(session_id, "ai_raw.json"))
    geometry = _read_json(session_file(session_id, "geometry.json"))

    payload_text = json.dumps(result_json, ensure_ascii=False)
    _assert(result_json.get("ai_core_mode") == "THREE_PROVIDER_CONSENSUS", "ai_core_mode")
    _assert(result_json.get("detector") == "YOLOv8", "detector")
    _assert(result_json.get("runtime_mode") == "PLAN_C_SYSTEM_C", "runtime_mode")
    _assert(result_json.get("model_policy") in {"system_c_detector", "single_class_pohon_sono"}, "model_policy")
    _assert(result_json.get("zone_overlay_status") == "ZONE_OVERLAY_RENDERED", "zone overlay rendered")
    _assert(result_json.get("risk_status") in ALLOWED_RISKS, f"risk_status {result_json.get('risk_status')}")
    _assert("prediction_window" in result_json, "prediction_window exists")
    _assert("DATA_TIDAK_CUKUP_KONDUKTOR_TIDAK_TERVALIDASI" not in payload_text, "no conductor hard blocker")
    _assert(result_json.get("multi_class_runtime") is not True, "no multi_class_runtime true")
    _assert(result_json.get("conductor_required_for_detection") is not True, "no conductor_required_for_detection true")
    _assert("AI detected" not in payload_text, "no AI detected wording")
    _assert(ai_raw.get("ai_core_mode") == "THREE_PROVIDER_CONSENSUS", "ai_raw core mode")
    provider_names = {item.get("provider") for item in ai_raw.get("provider_results", []) if isinstance(item, dict)}
    _assert({"gemini", "groq", "openrouter"}.issubset(provider_names), f"provider set {provider_names}")
    _assert("xai" not in provider_names and "grok/xai" not in provider_names, "xAI is not an active provider")
    _assert(geometry.get("zone_overlay_status") == "ZONE_OVERLAY_RENDERED", "geometry zone overlay rendered")
    _assert(count_csv_rows(PLAN_C_RECORDS_CSV) == csv_before + 1, "CSV append-only")
    _assert(count_jsonl_rows(PLAN_C_RECORDS_JSONL) == jsonl_before + 1, "JSONL append-only")

    summary = {
        "status": "PLAN_C_AI_BACKEND_SYSTEM_C_SMOKE_PASS",
        "session_id": session_id,
        "provider_keys_present": provider_keys,
        "provider_priority": provider_config.get("provider_priority", []),
        "local_detector_status": result_json.get("yolo_status"),
        "final_detection_source": result_json.get("final_detection_source"),
        "zone_overlay_status": result_json.get("zone_overlay_status"),
        "zone_method": result_json.get("zone_method"),
        "risk_status": result_json.get("risk_status"),
        "prediction_window": result_json.get("prediction_window"),
        "annotated_image_path": str(annotated_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("PLAN_C_AI_BACKEND_SYSTEM_C_SMOKE_PASS")
    return 0


def _build_tree_image_bytes() -> bytes:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (720, 960), (180, 200, 222))
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 720, 320], fill=(168, 188, 210))
    draw.rectangle([0, 320, 720, 650], fill=(176, 168, 126))
    draw.rectangle([0, 650, 720, 960], fill=(88, 128, 75))
    draw.rectangle([338, 420, 382, 880], fill=(94, 58, 34))
    draw.ellipse([120, 120, 610, 600], fill=(31, 125, 62))
    draw.ellipse([205, 70, 530, 390], fill=(37, 148, 70))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=91)
    return buffer.getvalue()


def _load_local_secrets_env() -> None:
    path = ROOT / "config" / "secrets.env"
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
