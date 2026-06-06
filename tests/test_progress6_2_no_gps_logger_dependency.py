from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_RUNTIME_FILES = [
    ROOT / "src" / "ulp_project" / "field_session_runtime.py",
    ROOT / "src" / "ulp_project" / "field_capture_routes.py",
    ROOT / "src" / "ulp_project" / "static" / "field_session.js",
    ROOT / "src" / "ulp_project" / "templates" / "field_capture.html",
    ROOT / "src" / "ulp_project" / "templates" / "field_report.html",
    ROOT / "src" / "ulp_project" / "templates" / "field_result.html",
    ROOT / "src" / "ulp_project" / "templates" / "field_manual_input.html",
]


def test_progress6_2_active_runtime_has_no_gps_logger_dependency() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in ACTIVE_RUNTIME_FILES)

    for forbidden in ["GPS Logger", "GPSLogger", "download GPS", "install aplikasi GPS", "Google Geolocation API"]:
        assert forbidden not in combined
