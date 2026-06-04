from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress5_4_favicon_returns_no_content_not_500() -> None:
    response = create_app().test_client().get("/favicon.ico")

    assert response.status_code == 204
