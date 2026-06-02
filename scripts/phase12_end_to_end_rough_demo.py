from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.realtime_field_pipeline import process_realtime_inspection  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 12 rough end-to-end demo.")
    parser.add_argument("--with-sample-gps", action="store_true")
    args = parser.parse_args(argv)
    payload = {
        "inspection_id": "DEMO_SAMPLE_NOT_FIELD_DATA",
        "point_id": "V001_pohon_sono_demo",
        "species": "pohon_sono",
        "asset_type": "span",
        "clearance_m": 0.30,
        "growth_rate_m_per_day": 0.01,
        "measurement_source": "manual",
        "confidence_status": "PROVISIONAL",
        "notes": "DEMO_SAMPLE_NOT_FIELD_DATA",
    }
    if args.with_sample_gps:
        payload.update({"latitude": "-7.000000", "longitude": "112.000000"})
    result = process_realtime_inspection(payload, write_outputs=True)
    passed = result["eta_days"] == 30.0 and result["report_written"] is True
    print(json.dumps({**result, "status": "PHASE12_END_TO_END_ROUGH_DEMO_PASS" if passed else "PHASE12_END_TO_END_ROUGH_DEMO_FAIL"}, indent=2, ensure_ascii=False))
    print("PHASE12_END_TO_END_ROUGH_DEMO_PASS" if passed else "PHASE12_END_TO_END_ROUGH_DEMO_FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
