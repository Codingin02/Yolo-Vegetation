from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def main() -> int:
    app = create_app()
    client = app.test_client()
    payload = {
        "point_id": "V001_pohon_sono",
        "species": "pohon_sono",
        "asset_type": "span",
        "latitude": "-7.000000",
        "longitude": "112.000000",
        "clearance_m": "0.30",
        "growth_rate_m_per_day": "0.01",
        "notes": "synthetic_test_only_not_field_data",
    }
    response = client.post("/api/field-capture/upload", json=payload)
    data = response.get_json() or {}
    checks = {
        "http_status": response.status_code,
        "eta_days": data.get("eta_days"),
        "eta_months": data.get("eta_months"),
        "risk_priority": data.get("risk_priority"),
        "report_written": data.get("report_written"),
        "map_marker_written": data.get("map_marker_written"),
        "job_id": data.get("job_id"),
    }
    passed = (
        response.status_code == 200
        and data.get("eta_days") == 30.0
        and data.get("risk_priority") == "CRITICAL"
        and data.get("report_written") is True
        and data.get("map_marker_written") is True
    )
    print(json.dumps({**checks, "status": "PHASE10_ROUGH_FIELD_CAPTURE_DEPLOY_PASS" if passed else "PHASE10_ROUGH_FIELD_CAPTURE_DEPLOY_FAIL"}, indent=2, ensure_ascii=False))
    print("PHASE10_ROUGH_FIELD_CAPTURE_DEPLOY_PASS" if passed else "PHASE10_ROUGH_FIELD_CAPTURE_DEPLOY_FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
