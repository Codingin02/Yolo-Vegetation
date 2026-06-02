import pytest

from ulp_project.flask_app import create_app, get_model_state


def test_model_state_is_not_ready_without_final_weights():
    assert get_model_state()["status"] == "MODEL_NOT_READY"


def test_flask_contract_routes_without_starting_server():
    try:
        app = create_app()
    except RuntimeError as exc:
        if "FLASK_NOT_INSTALLED" in str(exc):
            pytest.skip(str(exc))
        raise
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert {"/health", "/status", "/classes", "/points", "/map", "/predict-image"}.issubset(rules)
