from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_3_glass_ui_has_acceptance_navigation_and_mobile_guards() -> None:
    capture = (ROOT / "src" / "ulp_project" / "templates" / "field_capture.html").read_text(encoding="utf-8")
    css = (ROOT / "src" / "ulp_project" / "static" / "field_capture_glass.css").read_text(encoding="utf-8")
    nav = (ROOT / "src" / "ulp_project" / "static" / "field_navigation.js").read_text(encoding="utf-8")

    assert 'id="session-acceptance"' in capture
    assert "bind(\"session-acceptance\", \"/field-acceptance\")" in nav
    assert "backdrop-filter: blur(18px)" in css
    assert "border-radius: 28px" in css
    assert "position: sticky" in css
    assert "prefers-reduced-motion" in css
    assert "overflow-x: hidden" in css
