from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.environmental_fetcher import build_fetch_request, fetch_environmental_data  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch or dry-run environmental data cache safely.")
    parser.add_argument("--point", default="V001_pohon_sono")
    parser.add_argument("--lat", type=float, default=None)
    parser.add_argument("--lon", type=float, default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--mode", choices=["dry-run", "fetch"], default="dry-run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request = build_fetch_request(args.point, args.lat, args.lon, args.date, args.mode)
    result = fetch_environmental_data(request)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
