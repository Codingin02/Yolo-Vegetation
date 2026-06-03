from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.realtime_field_pipeline import process_realtime_inspection  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 11 provisional ETA demo without YOLO/training.")
    parser.add_argument("--point-id", default="V001_pohon_sono")
    parser.add_argument("--species", default="pohon_sono")
    parser.add_argument("--asset-type", default="span")
    parser.add_argument("--clearance-m", type=float, default=5.0)
    parser.add_argument("--growth-rate-m-per-day", type=float, default=0.01)
    parser.add_argument("--lat", default="")
    parser.add_argument("--lon", default="")
    args = parser.parse_args(argv)
    result = process_realtime_inspection(
        {
            "point_id": args.point_id,
            "species": args.species,
            "asset_type": args.asset_type,
            "clearance_m": args.clearance_m,
            "growth_rate_m_per_day": args.growth_rate_m_per_day,
            "latitude": args.lat,
            "longitude": args.lon,
            "measurement_source": "manual",
            "confidence_status": "PROVISIONAL",
            "notes": "Phase 11 provisional demo, not final accuracy.",
        },
        write_outputs=True,
    )
    status = "PHASE11_PROVISIONAL_ETA_RISK_READY" if result["eta_days"] == 200.0 and result["risk_priority"] == "LOW" else "PHASE11_PROVISIONAL_ETA_RISK_FAIL"
    print(json.dumps({**result, "demo_status": status}, indent=2, ensure_ascii=False))
    print(status)
    return 0 if status.endswith("_READY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
