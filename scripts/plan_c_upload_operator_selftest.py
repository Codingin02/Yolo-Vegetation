from __future__ import annotations

from io import BytesIO
import base64
import json
from pathlib import Path
import sys
from typing import Any

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

FALLBACK_JPEG_BYTES = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QA"
    "FQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oA"
    "CAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/Aaf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/Aaf/xAAU"
    "EAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Aqf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/E"
    "ABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAAAAA"
    "AAAAAAAAABD/2gAIAQEAAT8QH//Z"
)


def make_test_jpeg() -> bytes:
    try:
        from PIL import Image

        buffer = BytesIO()
        image = Image.new("RGB", (128, 96), color=(65, 124, 92))
        image.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()
    except Exception:
        return FALLBACK_JPEG_BYTES


def main() -> int:
    summary: dict[str, Any] = {
        "status": "PLAN_C_UPLOAD_OPERATOR_SELFTEST_FAILED",
        "training_ran": False,
        "runtime_deleted": False,
        "checks": {},
    }
    try:
        app = create_app()
        client = app.test_client()
        model_status = get_plan_c_ai_model_status()
        summary["model_status"] = model_status.get("status")
        summary["model_path"] = model_status.get("model_path")

        upload_page = client.get("/plan-c/upload")
        summary["checks"]["route_upload_200"] = upload_page.status_code == 200

        csv_before = count_csv_rows(PLAN_C_RECORDS_CSV)
        jsonl_before = count_jsonl_rows(PLAN_C_RECORDS_JSONL)
        markers_before = len(read_markers())

        start = client.post(
            "/api/plan-c/upload/start",
            data={
                "image": (BytesIO(make_test_jpeg()), "operator_selftest.jpg"),
                "latitude": "-7.231",
                "longitude": "112.735",
                "accuracy_m": "6.2",
                "operator_name": "operator_selftest",
                "point_id": "OPERATOR_SELFTEST_UPLOAD",
                "notes": "Plan C upload operator self-test",
                "source_mode": "UPLOAD_IMAGE_MODE",
            },
            content_type="multipart/form-data",
        )
        start_json = start.get_json(silent=True) or {}
        session_id = start_json.get("session_id")
        summary["session_id"] = session_id
        summary["checks"]["upload_start_201"] = start.status_code == 201
        summary["checks"]["metadata_json_created"] = bool(session_id and session_file(session_id, "metadata.json").exists())

        process = client.post(f"/api/plan-c/upload/process/{session_id}") if session_id else None
        process_json = process.get_json(silent=True) if process is not None else {}
        result = (process_json or {}).get("result") or {}
        summary["checks"]["manual_process_200"] = bool(process is not None and process.status_code == 200)
        summary["process_status"] = (process_json or {}).get("status")
        summary["risk_status"] = result.get("risk_status")
        summary["detection_status"] = result.get("detection_status")
        summary["manual_review_required"] = result.get("manual_review_required")

        summary["checks"]["result_json_created"] = bool(session_id and session_file(session_id, "result.json").exists())
        summary["checks"]["annotated_jpg_created"] = bool(session_id and session_file(session_id, "annotated.jpg").exists())
        summary["checks"]["developer_page_200"] = bool(
            session_id and client.get(f"/plan-c/upload/developer/{session_id}").status_code == 200
        )
        summary["checks"]["result_page_200"] = bool(
            session_id and client.get(f"/plan-c/upload/result/{session_id}").status_code == 200
        )

        csv_after = count_csv_rows(PLAN_C_RECORDS_CSV)
        jsonl_after = count_jsonl_rows(PLAN_C_RECORDS_JSONL)
        markers_after = len(read_markers())
        summary["csv_rows_before"] = csv_before
        summary["csv_rows_after"] = csv_after
        summary["jsonl_rows_before"] = jsonl_before
        summary["jsonl_rows_after"] = jsonl_after
        summary["markers_before"] = markers_before
        summary["markers_after"] = markers_after
        summary["checks"]["csv_append_only_incremented"] = csv_after == csv_before + 1
        summary["checks"]["jsonl_append_only_incremented"] = jsonl_after == jsonl_before + 1
        summary["checks"]["gps_marker_incremented_when_valid"] = markers_after == markers_before + 1

        failed = [name for name, ok in summary["checks"].items() if not ok]
        summary["failed_checks"] = failed
        if failed:
            print(json.dumps(summary, indent=2, sort_keys=True))
            return 1

        summary["status"] = "PLAN_C_UPLOAD_OPERATOR_SELFTEST_PASS"
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        summary["error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
