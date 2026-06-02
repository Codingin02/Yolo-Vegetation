from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.report_export import build_operator_report, export_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export operator system report.")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    args = parser.parse_args(argv)
    report = build_operator_report(ROOT)
    result = export_report(report, mode=args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {"SYSTEM_REPORT_DRY_RUN_READY", "SYSTEM_REPORT_WRITTEN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
