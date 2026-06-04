from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_1_labeling import validate_label_export  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MakeSense YOLO export without creating fake labels.")
    parser.add_argument("--export-dir", action="append", type=Path, help="Optional explicit export folder. Can be repeated.")
    parser.add_argument("--write-reports", action="store_true")
    args = parser.parse_args()
    result = validate_label_export(args.export_dir, write_reports=args.write_reports)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    if result["status"] == "MAKESENSE_EXPORT_NOT_FOUND":
        print("PROGRESS_6_1_LABELING_HANDOFF_READY_WAITING_FOR_MAKESENSE_EXPORT")
        return 0
    return 0 if result["status"] == "LABEL_EXPORT_VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
