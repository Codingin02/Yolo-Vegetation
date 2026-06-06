from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app


def run_smoke() -> dict[str, object]:
    report_html = (ROOT / "src" / "ulp_project" / "templates" / "field_report.html").read_text(encoding="utf-8")
    result_html = (ROOT / "src" / "ulp_project" / "templates" / "field_result.html").read_text(encoding="utf-8")
    required_report = [
        "Session Evidence",
        "GPS Evidence",
        "Camera/Frame Evidence",
        "AI/Model Evidence",
        "Geometry/Measurement Evidence",
        "Operator Notes",
        "CSV/Map Links",
        "Limitations",
    ]
    required_result = [
        "result_status",
        "confidence_status",
        "measurement_quality_label",
        "action_recommendation",
        "MODEL_NOT_READY",
        "CALIBRATION_NOT_READY_CLEARANCE_NOT_FINAL",
    ]
    with TemporaryDirectory() as tmp:
        app = create_app(runtime_root=Path(tmp))
        client = app.test_client()
        routes_ok = client.get("/field-report").status_code == 200 and client.get("/field-result").status_code == 200
        latest = client.get("/api/field/latest-result").get_json() or {}
    missing = [item for item in required_report if item not in report_html] + [item for item in required_result if item not in result_html]
    ok = routes_ok and not missing and latest.get("zone_status") == "INSUFFICIENT_DATA" and latest.get("result_status") == "MODEL_NOT_READY_NO_AI_DETECTION"
    return {
        "status": "PROGRESS_6_3_REPORT_RESULT_SMOKE_PASS" if ok else "PROGRESS_6_3_REPORT_RESULT_HARDENING_FAILED",
        "missing": missing,
        "latest_result_status": latest.get("status"),
        "latest_zone_status": latest.get("zone_status"),
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PROGRESS_6_3_REPORT_RESULT_SMOKE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
