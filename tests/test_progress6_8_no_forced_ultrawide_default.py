from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_8_no_forced_ultrawide_default() -> None:
    html = (ROOT / "src" / "ulp_project" / "templates" / "field_camera.html").read_text(encoding="utf-8")
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    assert 'facingMode: { ideal: "environment" }' in js
    assert 'facingMode: { exact: "environment" }' not in js
    assert "isUltraWideLabel" in js
    assert "Ultra-wide hanya dipakai bila operator memilihnya" in html
