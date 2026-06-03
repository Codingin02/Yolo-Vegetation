from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.environmental_manual_loader import validate_environmental_manual_csv  # noqa: E402
from ulp_project.environmental_source_registry import source_availability_summary  # noqa: E402


def main() -> int:
    manual = validate_environmental_manual_csv()
    sources = source_availability_summary()
    checks = {
        "registry_ready": sources["status"] == "ENVIRONMENT_SOURCE_REGISTRY_READY",
        "manual_template_available": manual["status"] in {"MANUAL_ENVIRONMENT_READY", "ENVIRONMENT_MANUAL_TEMPLATE_PARTIAL"},
        "no_api_key_required": sources["no_api_key_required"] is True,
    }
    status = "PHASE18_ENVIRONMENTAL_LAYER_READY" if all(checks.values()) else "PHASE18_ENVIRONMENTAL_LAYER_FAIL"
    print(json.dumps({"status": status, "checks": checks, "manual": manual, "sources": sources}, indent=2, ensure_ascii=False))
    print(status)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
