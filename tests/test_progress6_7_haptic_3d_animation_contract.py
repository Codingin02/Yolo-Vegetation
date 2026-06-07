from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_7_haptic_and_3d_animation_contract() -> None:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    css = (ROOT / "src" / "ulp_project" / "static" / "field_camera.css").read_text(encoding="utf-8")
    assert "safeVibrate" in js
    assert "navigator.vibrate" in js
    assert "press3D" in js
    assert "shutterPulse" in js
    assert "press-3d-active" in css
    assert "shutterPulse3d" in css
    assert "prefers-reduced-motion: reduce" in css
