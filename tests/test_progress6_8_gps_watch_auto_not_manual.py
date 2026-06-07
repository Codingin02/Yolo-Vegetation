from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_8_gps_watch_auto_not_manual_primary() -> None:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    capture = (ROOT / "src" / "ulp_project" / "templates" / "field_capture.html").read_text(encoding="utf-8")
    assert "watchPosition" in js
    assert "enableHighAccuracy: true" in js
    assert "browser_watchPosition" in js or "GPS_SOURCE_BROWSER" in js
    assert "GPS_SOURCE_MANUAL" not in js
    assert 'id="lat"' in capture and 'type="hidden"' in capture
