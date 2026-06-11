from ulp_project.flask_app import create_app


def test_plan_c_routes_return_controlled_responses():
    app = create_app()
    client = app.test_client()
    session_id = client.post("/api/plan-c/session/start", json={}).get_json()["session_id"]

    routes = [
        "/plan-c",
        f"/plan-c/capture/{session_id}",
        f"/plan-c/processing/{session_id}",
        f"/plan-c/result/{session_id}",
        f"/plan-c/developer/{session_id}",
        "/plan-c/map",
        "/api/plan-c/runtime/ui-version",
        f"/api/plan-c/session/{session_id}/status",
        f"/api/plan-c/session/{session_id}/result",
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code < 500, route


def test_plan_c_ui_version_route():
    app = create_app()
    response = app.test_client().get("/api/plan-c/runtime/ui-version")
    assert response.status_code == 200
    assert response.get_json()["plan_c_ui_version"] == "progress8_1_plan_c_field_trial_hardening"
