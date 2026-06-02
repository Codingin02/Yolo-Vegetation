from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.vegetation_risk_model import score_pohon_sono_risk  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 6 pohon_sono risk skeleton safely.")
    parser.add_argument("--point", default="V001_pohon_sono")
    parser.add_argument("--lat", type=float, default=None)
    parser.add_argument("--lon", type=float, default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--mode", choices=["dry-run", "sample-risk"], default="dry-run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = {
        "point_id": args.point,
        "latitude": args.lat,
        "longitude": args.lon,
        "observation_date": args.date,
        "species": "pohon_sono",
    }
    result = score_pohon_sono_risk(payload)
    result["mode"] = args.mode
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
