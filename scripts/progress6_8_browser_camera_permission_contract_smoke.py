from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_smoke() -> dict[str, object]:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    camera_html = (ROOT / "src" / "ulp_project" / "templates" / "field_camera.html").read_text(encoding="utf-8")
    css = (ROOT / "src" / "ulp_project" / "static" / "field_camera.css").read_text(encoding="utf-8")
    checks = {
        "uses_get_user_media": "getUserMedia" in js,
        "uses_enumerate_devices": "enumerateDevices" in js,
        "uses_device_id_switching": "deviceId" in js and "camera-lens-select" in camera_html,
        "ideal_environment_default": 'facingMode: { ideal: "environment" }' in js,
        "no_exact_environment_default": 'facingMode: { exact: "environment" }' not in js,
        "camera_error_permission_denied": "CAMERA_PERMISSION_DENIED" in js,
        "camera_error_constraint_failed": "CAMERA_CONSTRAINT_FAILED" in js,
        "camera_error_not_readable": "CAMERA_NOT_READABLE" in js,
        "ultrawide_not_default": "isUltraWideLabel" in js and "Ultra-wide hanya dipakai bila operator memilihnya" in camera_html,
        "stops_old_tracks_on_switch": "getTracks().forEach" in js and "track.stop()" in js,
        "lens_sheet_ui": "camera-lens-sheet" in camera_html and "camera-lens-button" in css,
    }
    return {
        "status": "PROGRESS_6_8_BROWSER_CAMERA_PERMISSION_CONTRACT_PASS" if all(checks.values()) else "PROGRESS_6_8_BROWSER_CAMERA_PERMISSION_CONTRACT_FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
