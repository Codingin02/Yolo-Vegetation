from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress6_2_glass_ui_routes_are_available() -> None:
    client = create_app().test_client()
    expected = {
        "/field-capture": ["Monitoring Vegetasi 20 kV", "session-start", "field_capture_glass.css"],
        "/field-report": ["Field Report", "Download CSV", "field_capture_glass.css"],
        "/field-result": ["Field Result", "FIELD_RESULT_PROVISIONAL", "field_capture_glass.css"],
        "/field-manual-input": ["Manual Input", "MANUAL_OPERATOR_INPUT_NOT_AI_DETECTION", "field_capture_glass.css"],
    }

    for route, tokens in expected.items():
        response = client.get(route)
        html = response.get_data(as_text=True)
        assert response.status_code == 200
        for token in tokens:
            assert token in html
