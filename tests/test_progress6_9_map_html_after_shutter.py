from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_9_map_html_after_shutter_not_json(tmp_path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    session_id = client.post(
        "/api/field/session/start",
        json={"gps": {"latitude": -7.2234567, "longitude": 112.7312345, "accuracy": 5.0}},
    ).get_json()["session_id"]
    client.post("/api/field/session/shutter", json={"session_id": session_id, "idempotency_key": "P69_MAP"})
    response = client.get(f"/field-map/session/{session_id}")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    assert "<html" in html.lower()
    assert "MAP_HTML_READY" in html or "NO_GPS_NO_MARKER" in html
    assert '"status"' not in html[:80]
