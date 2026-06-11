from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_conductor_structure_acquisition import acquire_conductor_references  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire legal overhead conductor candidates.")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = acquire_conductor_references(limit=args.limit, download=bool(args.download and not args.dry_run))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
