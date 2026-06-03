from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_hp_result_intake_route_writes_only_runtime_root(tmp_path: Path) -> None:
    app = create_app(runtime_root=tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/field-trial/hp-result",
        json={
            "network_type": "wifi",
            "public_url_opened": True,
            "server_connection_ok": True,
            "camera_ok": False,
            "gps_ok": False,
            "manual_prediction_ok": True,
            "snapshot_report_ok": True,
            "map_report_ok": True,
            "error_code": "CAMERA_PERMISSION_DENIED",
            "screenshot_base64": "SHOULD_NOT_BE_STORED",
        },
    )
    payload = response.get_json()

    assert response.status_code == 201
    assert payload["status"] == "HP_RESULT_RECORDED"
    assert "screenshot_base64" not in payload
    assert Path(payload["path"]).is_file()
    assert str(Path(payload["path"])).startswith(str(tmp_path / "field_trial_evidence"))


def test_progress5_3_routes_available_from_flask_app(tmp_path: Path) -> None:
    app = create_app(runtime_root=tmp_path)
    client = app.test_client()
    routes = {str(rule.rule) for rule in app.url_map.iter_rules()}

    assert "/field-trial-checklist" in routes
    assert "/api/runtime/tunnel-status" in routes
    assert "/api/operator/failure-recovery" in routes
    assert "HP membuka URL public tunnel" in client.get("/field-trial-checklist").get_data(as_text=True)
