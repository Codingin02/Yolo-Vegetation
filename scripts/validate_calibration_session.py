from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.calibration_workflow import validate_calibration_payload  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate calibration payload.")
    parser.add_argument("--known-height-m", type=float)
    parser.add_argument("--reference-bbox-height-px", type=float)
    parser.add_argument("--image-width-px", type=int)
    parser.add_argument("--image-height-px", type=int)
    args = parser.parse_args(argv)
    result = validate_calibration_payload(vars(args))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["quality_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
