from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.realtime_pipeline import run_realtime_field_pipeline  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 8 realtime field pipeline dry-run.")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    parser.add_argument("--point-id", default="V001_pohon_sono")
    parser.add_argument("--minimum-clearance-m", type=float, default=None)
    parser.add_argument("--base-growth-rate-m-per-day", type=float, default=None)
    parser.add_argument("--allow-provisional", action="store_true")
    args = parser.parse_args(argv)
    result = run_realtime_field_pipeline(
        {
            "point_id": args.point_id,
            "species": "pohon_sono",
            "minimum_clearance_m": args.minimum_clearance_m,
            "base_growth_rate_m_per_day": args.base_growth_rate_m_per_day,
        },
        mode=args.mode,
        allow_provisional=args.allow_provisional,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
