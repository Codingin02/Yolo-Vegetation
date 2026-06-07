from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_smoke() -> dict[str, object]:
    camera = (ROOT / "src" / "ulp_project" / "templates" / "field_camera.html").read_text(encoding="utf-8")
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    css = (ROOT / "src" / "ulp_project" / "static" / "field_camera.css").read_text(encoding="utf-8")
    bottom_start = camera.index('<nav class="camera-bottom-bar"')
    bottom_end = camera.index("</nav>", bottom_start)
    bottom = camera[bottom_start:bottom_end]
    order = [bottom.find(token) for token in ["session-home", "open-map-report", "shutter-capture", "session-result", "session-manual-input"]]
    checks = {
        "bottom_bar_order_home_map_shutter_result_manual": all(index >= 0 for index in order) and order == sorted(order),
        "no_report_button_in_camera_bottom_bar": "session-report" not in bottom and ">Report<" not in bottom,
        "map_result_disabled_before_shutter": 'id="open-map-report"' in bottom and 'id="session-result"' in bottom and "disabled" in bottom,
        "developer_debug_collapsed_default": "<details class=\"camera-debug\">" in camera,
        "developer_debug_max_40vh": "max-height: 40dvh" in css,
        "haptic_vibrate_exists": "safeVibrate" in js and "navigator.vibrate" in js,
        "press_3d_animation_exists": "press3D" in js and "press-3d-active" in css and "transform-style: preserve-3d" in css,
        "shutter_pulse_exists": "shutterPulse" in js and "shutterPulse3d" in css,
        "reduced_motion_guard": "prefers-reduced-motion: reduce" in css,
    }
    return {
        "status": "PROGRESS_6_7_CAMERA_UI_CONTRACT_PASS" if all(checks.values()) else "PROGRESS_6_7_CAMERA_UI_CONTRACT_FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
