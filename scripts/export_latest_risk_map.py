from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.folium_report_builder import build_latest_risk_map  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export latest risk map from a safe dry-run row.")
    parser.add_argument("--with-sample-gps", action="store_true")
    args = parser.parse_args(argv)
    row = {"point_id": "V001_pohon_sono", "species": "pohon_sono", "risk_priority": "INSUFFICIENT_DATA", "confidence_status": "MODEL_NOT_READY"}
    if args.with_sample_gps:
        row.update({"latitude": -7.0, "longitude": 112.0, "operator_notes": "SYNTHETIC_TEST_ONLY_NOT_FIELD_DATA"})
    result = build_latest_risk_map(row)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
