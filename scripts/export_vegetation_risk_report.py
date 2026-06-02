from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.spreadsheet_report_writer import build_phase8_report_row, write_phase8_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Phase 8 vegetation risk spreadsheet report.")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    args = parser.parse_args(argv)
    row = build_phase8_report_row({"point_id": "V001_pohon_sono"})
    result = write_phase8_report([row], mode=args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
