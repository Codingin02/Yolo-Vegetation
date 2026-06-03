from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.calibration_workflow import create_calibration_session  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create runtime field calibration session.")
    parser.add_argument("--point-id", required=True)
    parser.add_argument("--reference-type", default="manual_reference")
    parser.add_argument("--known-height-m", type=float)
    parser.add_argument("--reference-bbox-height-px", type=float)
    parser.add_argument("--image-width-px", type=int)
    parser.add_argument("--image-height-px", type=int)
    parser.add_argument("--camera-device-hint", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    result = create_calibration_session(vars(args), write_runtime=not args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
