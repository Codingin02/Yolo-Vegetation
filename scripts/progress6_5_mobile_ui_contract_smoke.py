from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_smoke() -> dict[str, object]:
    capture = (ROOT / "src" / "ulp_project" / "templates" / "field_capture.html").read_text(encoding="utf-8")
    report = (ROOT / "src" / "ulp_project" / "templates" / "field_report.html").read_text(encoding="utf-8")
    result = (ROOT / "src" / "ulp_project" / "templates" / "field_result.html").read_text(encoding="utf-8")
    css = (ROOT / "src" / "ulp_project" / "static" / "field_capture_glass.css").read_text(encoding="utf-8")
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    legacy_js = (ROOT / "src" / "ulp_project" / "static" / "field_capture.js").read_text(encoding="utf-8")
    checks = {
        "fullscreen_camera_stage": "camera-stage" in capture and "camera-mode-active" in css and "100dvh" in css,
        "horizontal_camera_controls": "camera-bottom-bar" in capture and "grid-template-columns: repeat(6" in css,
        "shutter_client_idempotency": "shutterInFlight" in js and "idempotency_key" in js,
        "legacy_shutter_not_bound_to_main_button": 'addClick("legacy-shutter-capture", shutterCapture)' in legacy_js,
        "developer_debug_collapsible": "Developer Debug" in capture and "<details" in capture,
        "mobile_no_overflow_contract": "overflow-wrap: anywhere" in css and "word-break: break-word" in css and "max-width: 480px" in css,
        "report_simplified": "Session Evidence" in report and "Developer Detail" in report and "evidence-section-grid" in report,
        "result_simplified": "Status Operator" in result and "Reason Codes" in result and "Developer Detail" in result,
    }
    return {
        "status": "PROGRESS_6_5_MOBILE_UI_CONTRACT_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_5_MOBILE_UI_CONTRACT_SMOKE_FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
