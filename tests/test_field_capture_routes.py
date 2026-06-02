import pytest

from ulp_project.flask_app import create_app


def test_field_capture_available_and_mobile_is_alias(tmp_path):
    try:
        app = create_app(runtime_root=tmp_path)
    except RuntimeError as exc:
        if "FLASK_NOT_INSTALLED" in str(exc):
            pytest.skip(str(exc))
        raise
    client = app.test_client()
    assert client.get("/field-capture").status_code == 200
    mobile = client.get("/mobile")
    assert mobile.status_code in {301, 302}
    assert mobile.headers["Location"].endswith("/field-capture")
    assert client.get("/api/field-capture/ping").get_json()["status"] == "PONG"


def test_field_capture_upload_accepts_metadata_without_model(tmp_path):
    app = create_app(runtime_root=tmp_path)
    client = app.test_client()
    response = client.post("/api/field-capture/upload", data={"point_id": "V001_pohon_sono"})
    assert response.status_code == 202
    payload = response.get_json()
    assert payload["hp_role"] == "input_client_only"
    assert payload["processing_center"] == "laptop_flask_server"
