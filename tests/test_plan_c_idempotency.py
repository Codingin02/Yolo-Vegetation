import base64
from io import BytesIO
import uuid

from ulp_project.flask_app import create_app
from ulp_project.plan_c_storage import PLAN_C_RECORDS_CSV, PLAN_C_RECORDS_JSONL, count_csv_rows, count_jsonl_rows


def test_plan_c_snapshot_idempotency_prevents_duplicate_append():
    app = create_app()
    client = app.test_client()
    session_id = client.post("/api/plan-c/session/start", json={}).get_json()["session_id"]
    key = f"{session_id}:{uuid.uuid4()}"
    payload = {
        "session_id": session_id,
        "idempotency_key": key,
        "image_data": "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes()).decode("ascii"),
        "latitude": -7.231,
        "longitude": 112.735,
        "gps_accuracy_m": 8,
        "gps_status": "GPS_READY",
    }
    csv_before = count_csv_rows(PLAN_C_RECORDS_CSV)
    jsonl_before = count_jsonl_rows(PLAN_C_RECORDS_JSONL)

    first = client.post("/api/plan-c/session/snapshot", json=payload)
    assert first.status_code in {200, 201, 202}
    assert first.get_json()["status"] == "PLAN_C_RESULT_READY"

    duplicate = client.post("/api/plan-c/session/snapshot", json=payload)
    assert duplicate.status_code in {200, 202}
    assert duplicate.get_json()["duplicate_ignored"] is True
    assert count_csv_rows(PLAN_C_RECORDS_CSV) == csv_before + 1
    assert count_jsonl_rows(PLAN_C_RECORDS_JSONL) == jsonl_before + 1


def _jpeg_bytes() -> bytes:
    from PIL import Image

    image = Image.new("RGB", (24, 18), color=(50, 70, 90))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()
