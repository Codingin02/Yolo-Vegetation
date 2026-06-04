from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_2_training import progress6_2_training_policy_status  # noqa: E402


def main() -> int:
    result = progress6_2_training_policy_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
