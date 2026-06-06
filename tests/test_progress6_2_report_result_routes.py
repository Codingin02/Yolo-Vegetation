from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_2_latest_report_and_result_routes(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    started = client.post(
        "/api/field/session/start",
        json={
            "session_id": "TEST_REPORT_RESULT",
            "base_gps": {"latitude": -7.1, "longitude": 112.7, "accuracy": 6, "source": "GPS_SOURCE_BROWSER"},
        },
    ).get_json()
    session_id = started["session_id"]

    client.post(
        "/api/field/session/gps-update",
        json={"session_id": session_id, "latitude": -7.1002, "longitude": 112.7, "accuracy": 6, "source": "GPS_SOURCE_BROWSER"},
    )
    report = client.get(f"/api/field/latest-report?session_id={session_id}").get_json()
    result = client.get(f"/api/field/latest-result?session_id={session_id}").get_json()

    assert report["session_id"] == session_id
    assert report["report_page_url"].startswith("/field-report")
    assert result["session_id"] == session_id
    assert result["status"] == "MODEL_NOT_READY_NO_FAKE_DETECTION"
    assert "INSUFFICIENT_GEOMETRY_DATA" in result["reason_codes"]
