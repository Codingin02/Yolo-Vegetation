from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_5_no_marker_without_valid_gps(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    client.post(
        "/api/field/session/start",
        json={
            "session_id": "P65_INVALID_GPS",
            "source_mode": "SMOKE_TEST",
            "base_gps": {"latitude": 0, "longitude": 0, "accuracy": 4},
        },
    )

    result = client.get("/api/field/latest-map?session_id=P65_INVALID_GPS").get_json()
    html = client.get("/field-map/session/P65_INVALID_GPS").get_data(as_text=True)

    assert result["status"] == "NO_GPS_NO_MARKER"
    assert "INVALID_COORDINATE_ZERO_ZERO" in result["gps_quality_reasons"]
    assert "GPS belum valid, marker tidak dibuat." in html
