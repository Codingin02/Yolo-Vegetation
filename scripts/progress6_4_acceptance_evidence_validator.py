from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.field_acceptance_validation import validate_latest_acceptance

NONFATAL_STATUSES = {
    "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST",
    "PHYSICAL_HP_ACCEPTANCE_PASS",
    "PHYSICAL_HP_ACCEPTANCE_PASS_WITH_GPS_LIMITATION",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate latest live HP acceptance evidence.")
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    result = validate_latest_acceptance(args.runtime_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("acceptance_status") in NONFATAL_STATUSES else 1


if __name__ == "__main__":
    raise SystemExit(main())
