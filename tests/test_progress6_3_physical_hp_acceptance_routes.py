from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_3_physical_hp_acceptance_routes(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    assert client.get("/field-acceptance").status_code == 200

    started = client.post(
        "/api/field/acceptance/start",
        json={"session_id": "ACCEPTANCE_ROUTE_TEST", "secure_context_status": "SECURE_CONTEXT_OK"},
    ).get_json()
    assert started["status"] == "FIELD_ACCEPTANCE_STARTED"
    assert started["acceptance_status"] == "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"

    assert client.get("/api/field/acceptance/latest").status_code == 200
    assert client.get("/api/field/acceptance/evidence").status_code == 200
    assert client.get("/api/field/acceptance/status").status_code == 200
