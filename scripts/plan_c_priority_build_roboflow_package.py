from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_roboflow_priority_package import build_roboflow_priority_package  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Plan C Roboflow review package.")
    parser.add_argument("--mode", choices=["dry-run", "build"], default="dry-run")
    parser.add_argument("--zip", action="store_true", dest="make_zip")
    args = parser.parse_args()
    result = build_roboflow_priority_package(mode=args.mode, make_zip=args.make_zip)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
