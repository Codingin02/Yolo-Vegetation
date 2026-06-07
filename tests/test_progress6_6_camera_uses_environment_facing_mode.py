from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_6_camera_uses_environment_facing_mode_with_fallbacks() -> None:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    assert 'facingMode: { ideal: "environment" }' in js
    assert 'facingMode: "environment"' in js
    assert "video: true" in js
    assert "frameRate: { ideal: 30, max: 30 }" in js
