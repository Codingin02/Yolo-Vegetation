import pytest

from ulp_project.flask_app import create_app


def test_mobile_upload_accepts_metadata_without_model(tmp_path):
    try:
        app = create_app(runtime_root=tmp_path)
    except RuntimeError as exc:
        if "FLASK_NOT_INSTALLED" in str(exc):
            pytest.skip(str(exc))
        raise
    client = app.test_client()
    response = client.post(
        "/api/mobile/upload-inspection",
        data={"point_id": "V001_pohon_sono", "lat": "-7.0", "lon": "112.0", "network_mode": "same_lan_mode"},
    )
    assert response.status_code == 202
    payload = response.get_json()
    assert payload["status"] == "INSUFFICIENT_DATA"
    assert payload["model_status"] == "MODEL_NOT_READY"
    assert payload["not_accuracy_claim"] is True
    assert (tmp_path / "jobs").exists()
    assert (tmp_path / "results").exists()


def test_runtime_upload_folder_is_gitignored():
    gitignore = open(".gitignore", encoding="utf-8").read()
    assert "data/runtime/" in gitignore
