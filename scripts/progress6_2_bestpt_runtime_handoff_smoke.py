from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_2_training import progress6_2_bestpt_handoff_status  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Progress 6.2 best.pt runtime handoff smoke.")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    result = progress6_2_bestpt_handoff_status(args.model)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
