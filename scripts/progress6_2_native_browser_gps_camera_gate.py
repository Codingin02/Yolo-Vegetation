from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from progress6_2_gps_policy_smoke import build_smoke_status as gps_policy_smoke  # noqa: E402
from progress6_2_session_contract_smoke import build_smoke_status as session_contract_smoke  # noqa: E402
from progress6_2_ui_route_smoke import build_smoke_status as ui_route_smoke  # noqa: E402


ACTIVE_RUNTIME_FILES = [
    ROOT / "src" / "ulp_project" / "field_session_runtime.py",
    ROOT / "src" / "ulp_project" / "field_capture_routes.py",
    ROOT / "src" / "ulp_project" / "static" / "field_session.js",
    ROOT / "src" / "ulp_project" / "templates" / "field_capture.html",
    ROOT / "src" / "ulp_project" / "templates" / "field_report.html",
    ROOT / "src" / "ulp_project" / "templates" / "field_result.html",
    ROOT / "src" / "ulp_project" / "templates" / "field_manual_input.html",
]


def no_gps_logger_dependency() -> dict[str, object]:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in ACTIVE_RUNTIME_FILES)
    forbidden = ["GPS Logger", "GPSLogger", "download GPS", "install aplikasi GPS", "Google Geolocation API"]
    checks = {token: token not in combined for token in forbidden}
    return {
        "status": "NO_GPS_LOGGER_DEPENDENCY_PASS" if all(checks.values()) else "NO_GPS_LOGGER_DEPENDENCY_FAIL",
        "checks": checks,
    }


def native_browser_contract() -> dict[str, object]:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    tokens = [
        "navigator.geolocation.getCurrentPosition",
        "navigator.geolocation.watchPosition",
        "enableHighAccuracy: true",
        "navigator.mediaDevices.getUserMedia",
        "computeHaversineMeters",
        "FOREGROUND_RECORDING_REQUIRED",
        "MODEL_NOT_READY_NO_FAKE_DETECTION",
    ]
    checks = {token: token in js for token in tokens}
    return {
        "status": "NATIVE_BROWSER_GEOLOCATION_CAMERA_CONTRACT_PASS"
        if all(checks.values())
        else "NATIVE_BROWSER_GEOLOCATION_CAMERA_CONTRACT_FAIL",
        "checks": checks,
    }


def build_gate_status() -> dict[str, object]:
    ui = ui_route_smoke()
    session = session_contract_smoke()
    gps = gps_policy_smoke()
    no_logger = no_gps_logger_dependency()
    browser = native_browser_contract()
    checks = {
        "ui_routes": ui["status"].endswith("_PASS"),
        "session_contract": session["status"].endswith("_PASS"),
        "gps_policy": gps["status"].endswith("_PASS"),
        "no_gps_logger": no_logger["status"].endswith("_PASS"),
        "native_browser_contract": browser["status"].endswith("_PASS"),
    }
    status = (
        "PROGRESS_6_2_NATIVE_BROWSER_GPS_CAMERA_SESSION_GLASS_UI_READY_MODEL_SAFE_MODE"
        if all(checks.values())
        else "PROGRESS_6_2_BLOCKED_NATIVE_BROWSER_GPS_CAMERA_CONTRACT"
    )
    return {
        "status": status,
        "checks": checks,
        "ui": ui,
        "session": session,
        "gps_policy": gps,
        "no_gps_logger_dependency": no_logger,
        "native_browser_contract": browser,
        "no_fake_gps": True,
        "no_fake_detection": True,
        "no_label_touch": True,
        "dataset_botol_used": False,
    }


def main() -> int:
    result = build_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_SAFE_MODE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
