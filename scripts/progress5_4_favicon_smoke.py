from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    response = create_app().test_client().get("/favicon.ico")
    checks = {"favicon_not_500": response.status_code in {204, 404}, "favicon_status_code": response.status_code}
    return {"status": "PROGRESS5_4_FAVICON_SMOKE_PASS" if checks["favicon_not_500"] else "PROGRESS5_4_FAVICON_SMOKE_FAIL", "checks": checks}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
