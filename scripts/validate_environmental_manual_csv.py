from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.environmental_manual_loader import validate_environmental_manual_csv  # noqa: E402


def main() -> int:
    result = validate_environmental_manual_csv()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"] in {"MANUAL_ENVIRONMENT_READY", "ENVIRONMENT_MANUAL_TEMPLATE_PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
