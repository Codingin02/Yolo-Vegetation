from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402


def main() -> int:
    app = create_app()
    client = app.test_client()
    start = client.post("/api/plan-c/session/start", json={})
    _assert(start.status_code == 201, "session start failed")
    session_id = start.get_json().get("session_id")
    page = client.get(f"/plan-c/capture/{session_id}")
    _assert(page.status_code == 200, "capture page HTTP not 200")
    html = page.get_data(as_text=True)

    for required in [
        "Apakah Anda sudah berada tepat di bawah pohon yang akan diprediksi?",
        "pcv4-gallery",
        "pcv4-gallery-input",
        "accept=\"image/*\"",
        "pcv4-shutter",
        "pcv4-lens",
        "plan_c_fullscreen_camera_v4.css",
        "plan_c_fullscreen_camera_v4.js",
        "pcv4-bottom-nav",
        "Home",
        "Kamera",
        "Map",
        "Result",
    ]:
        _assert(required in html, f"capture page missing {required}")

    for forbidden in ["Camera ready", "GPS ready", "Server ready", "MODEL_STATUS_UNKNOWN", "YOLO-FIRST"]:
        _assert(forbidden not in html, f"operator capture page contains {forbidden}")

    css = (ROOT / "src" / "ulp_project" / "static" / "plan_c_fullscreen_camera_v4.css").read_text(encoding="utf-8")
    _assert(".pcv4-camera-controls" in css, "camera controls CSS missing")
    _assert("bottom: calc(env(safe-area-inset-bottom, 0px) + 98px)" in css, "shutter controls not above bottom nav")

    js = (ROOT / "src" / "ulp_project" / "static" / "plan_c_fullscreen_camera_v4.js").read_text(encoding="utf-8")
    for required in ["watchPosition", "enableHighAccuracy: true", "maximumAge: 0", "timeout: 10000", "haversineMeters", "ultrawide", "submitSnapshot(file, \"gallery\")"]:
        _assert(required in js, f"capture JS missing {required}")

    print("PLAN_C_CAPTURE_UI_V5_SMOKE_PASS")
    print(f"session_id={session_id}")
    return 0


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
