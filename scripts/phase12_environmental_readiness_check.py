from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.environmental_readiness import check_environmental_readiness  # noqa: E402


def main() -> int:
    result = check_environmental_readiness()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
