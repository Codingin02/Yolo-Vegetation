from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_8_static_cache_bust_tokens() -> None:
    for name in ["field_capture.html", "field_camera.html", "field_report.html", "field_result.html"]:
        text = (ROOT / "src" / "ulp_project" / "templates" / name).read_text(encoding="utf-8")
        assert "progress6_8" in text
    routes = (ROOT / "src" / "ulp_project" / "field_capture_routes.py").read_text(encoding="utf-8")
    assert '"ui_version": "progress6_8"' in routes
    assert "no-store" in routes
