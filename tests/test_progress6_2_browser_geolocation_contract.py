from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_progress6_2_uses_native_browser_geolocation_and_camera() -> None:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")

    for token in [
        "navigator.geolocation.getCurrentPosition",
        "navigator.geolocation.watchPosition",
        "enableHighAccuracy: true",
        "timeout: 15000",
        "maximumAge: 0",
        "navigator.mediaDevices.getUserMedia",
        'facingMode: { ideal: "environment" }',
        "FOREGROUND_RECORDING_REQUIRED",
    ]:
        assert token in js
