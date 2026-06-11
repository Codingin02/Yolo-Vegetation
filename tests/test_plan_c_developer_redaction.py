import base64
from io import BytesIO
import re
import uuid

from ulp_project.flask_app import create_app


def test_plan_c_developer_page_redacts_sensitive_and_image_payloads():
    app = create_app()
    client = app.test_client()
    session_id = client.post("/api/plan-c/session/start", json={}).get_json()["session_id"]
    payload = {
        "session_id": session_id,
        "idempotency_key": f"{session_id}:{uuid.uuid4()}",
        "image_data": "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes()).decode("ascii"),
        "latitude": -7.231,
        "longitude": 112.735,
        "gps_accuracy_m": 8,
        "gps_status": "GPS_READY",
    }
    assert client.post("/api/plan-c/session/snapshot", json=payload).status_code in {200, 201, 202}
    page = client.get(f"/plan-c/developer/{session_id}")
    text = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "OPENAI_API_KEY" not in text
    assert "GEMINI_API_KEY" not in text
    assert "GROQ_API_KEY" not in text
    assert "NGROK_AUTHTOKEN" not in text
    assert "SERVICE_ACCOUNT" not in text
    assert "credential" not in text
    assert "token" not in text
    assert "data:image" not in text
    assert not re.search(r"[A-Za-z0-9+/=]{240,}", text)


def _jpeg_bytes() -> bytes:
    from PIL import Image

    image = Image.new("RGB", (24, 18), color=(60, 90, 70))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()
