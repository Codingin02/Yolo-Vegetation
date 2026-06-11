import base64
from io import BytesIO
import re
import uuid

from ulp_project.flask_app import create_app


def test_free_vision_operator_result_hides_internal_names(monkeypatch):
    monkeypatch.setenv("PLAN_C_VISION_MODE", "free_only")
    monkeypatch.setenv("PLAN_C_OPERATOR_HIDE_PROVIDER", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", "")

    app = create_app()
    client = app.test_client()
    session_id = client.post("/api/plan-c/session/start", json={}).get_json()["session_id"]
    response = client.post(
        "/api/plan-c/session/snapshot",
        json={
            "session_id": session_id,
            "idempotency_key": f"{session_id}:{uuid.uuid4()}",
            "image_data": "data:image/jpeg;base64," + base64.b64encode(_jpeg_bytes()).decode("ascii"),
            "gps_status": "GPS_PERMISSION_DENIED",
        },
    )
    assert response.status_code in {200, 201, 202}

    result_page = client.get(f"/plan-c/result/{session_id}")
    assert result_page.status_code == 200
    text = result_page.get_data(as_text=True)
    for word in ["AI", "Gemini", "Groq", "OpenRouter", "LLM", "provider", "API key"]:
        assert not _contains_word(text, word), word

    developer_page = client.get(f"/plan-c/developer/{session_id}")
    developer_text = developer_page.get_data(as_text=True)
    for marker in ["GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "token", "credential"]:
        assert marker not in developer_text
    assert "data:image" not in developer_text
    assert not re.search(r"[A-Za-z0-9+/=]{240,}", developer_text)


def _jpeg_bytes() -> bytes:
    from PIL import Image

    image = Image.new("RGB", (32, 24), color=(40, 90, 64))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _contains_word(text: str, word: str) -> bool:
    if word in {"provider", "API key"}:
        return re.search(rf"\b{re.escape(word)}\b", text, flags=re.IGNORECASE) is not None
    return re.search(rf"\b{re.escape(word)}\b", text) is not None
