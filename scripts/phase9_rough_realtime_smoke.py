from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 9 rough realtime smoke using Flask local pipeline.")
    parser.add_argument("--with-sample-gps", action="store_true", help="Use synthetic_test_only GPS to verify map marker path.")
    args = parser.parse_args(argv)

    app = create_app()
    client = app.test_client()
    payload = {
        "point_id": "V001_pohon_sono_demo",
        "species": "pohon_sono",
        "asset_type": "span",
        "clearance_m": "5.0",
        "growth_rate_m_per_day": "0.01",
        "notes": "synthetic_test_only rough realtime smoke",
    }
    if args.with_sample_gps:
        payload.update({"latitude": "-7.000000", "longitude": "112.000000"})
    response = client.post("/api/field-capture/upload", json=payload)
    result = response.get_json()
    passed = bool(
        response.status_code == 200
        and result
        and result.get("eta_days") == 200.0
        and 6.56 <= float(result.get("eta_months")) <= 6.58
        and result.get("risk_priority") == "LOW"
        and result.get("report_written") is True
        and result.get("map_marker_written") is bool(args.with_sample_gps)
    )
    output = {
        "status": "PHASE9_ROUGH_REALTIME_SMOKE_PASS" if passed else "PHASE9_ROUGH_REALTIME_SMOKE_FAIL",
        "with_sample_gps": args.with_sample_gps,
        "http_status": response.status_code,
        "result": result,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
