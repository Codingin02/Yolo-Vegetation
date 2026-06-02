import pytest

from ulp_project.flask_app import create_app


def test_flask_phase5_api_routes_return_status_without_server():
    try:
        app = create_app()
    except RuntimeError as exc:
        if "FLASK_NOT_INSTALLED" in str(exc):
            pytest.skip(str(exc))
        raise
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/mobile").status_code in {301, 302}
    assert client.get("/field-capture").status_code == 200
    assert client.get("/api/status").status_code == 200
    assert client.get("/api/classes").get_json()["status"] == "LOCKED"
    assert client.get("/api/risk/sample").get_json()["status"] == "ENVIRONMENTAL_DATA_NOT_READY"
    response = client.post("/api/infer/image")
    assert response.status_code == 503
    assert response.get_json()["status"] == "MODEL_NOT_READY"
