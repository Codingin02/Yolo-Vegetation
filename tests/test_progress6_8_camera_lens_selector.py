from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_8_camera_lens_selector_contract() -> None:
    html = (ROOT / "src" / "ulp_project" / "templates" / "field_camera.html").read_text(encoding="utf-8")
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    assert "camera-lens-sheet" in html
    assert "camera-lens-select" in html
    assert "enumerateDevices" in js
    assert "deviceId" in js
    assert "getTracks().forEach" in js and "track.stop()" in js
