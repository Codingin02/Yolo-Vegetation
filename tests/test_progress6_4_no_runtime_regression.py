from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_4_core_routes_remain_available(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    for route in ["/field-capture", "/field-acceptance", "/field-report", "/field-result", "/field-manual-input"]:
        assert client.get(route).status_code == 200
    assert client.get("/favicon.ico").status_code == 204
