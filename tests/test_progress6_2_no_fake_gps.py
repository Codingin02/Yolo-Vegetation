from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_2_missing_gps_is_not_faked(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    started = client.post("/api/field/session/start", json={"session_id": "TEST_NO_FAKE_GPS"}).get_json()
    status = client.get(f"/api/field/session/status?session_id={started['session_id']}").get_json()

    assert status["no_fake_gps"] is True
    assert status["gps"]["base"]["latitude"] is None
    assert status["gps"]["base"]["longitude"] is None
    assert status["derived_gps"]["distance_reliability_status"] == "DISTANCE_NOT_AVAILABLE"
