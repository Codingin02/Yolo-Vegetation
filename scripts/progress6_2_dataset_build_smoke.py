from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_2_training import progress6_2_dataset_build_status  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Progress 6.2 dataset build smoke.")
    parser.add_argument("--mode", choices=["dry-run", "build"], default="dry-run")
    args = parser.parse_args()
    result = progress6_2_dataset_build_status(mode=args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if args.mode == "dry-run" else 0 if result["status"] == "DATASET_BUILD_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
