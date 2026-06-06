from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_5_capture_has_fullscreen_camera_mode_contract() -> None:
    html = (ROOT / "src" / "ulp_project" / "templates" / "field_capture.html").read_text(encoding="utf-8")
    css = (ROOT / "src" / "ulp_project" / "static" / "field_capture_glass.css").read_text(encoding="utf-8")
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")

    assert "camera-stage" in html
    assert "camera-bottom-bar" in html
    assert "field-toast" in html
    assert "camera-mode-active" in css
    assert "height: 100dvh" in css
    assert "object-fit: cover" in css
    assert "document.body.classList.add(\"camera-mode-active\")" in js
    assert "shutterInFlight" in js
    assert "SESSION_API_DEGRADED_FALLBACK_USED" in js
