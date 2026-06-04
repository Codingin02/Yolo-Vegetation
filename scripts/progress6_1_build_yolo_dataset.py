from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_1_labeling import FIELD_DATASET_DIR, build_yolo_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build YOLO dataset after MakeSense export validation.")
    parser.add_argument("--mode", choices=["dry-run", "build"], default="dry-run")
    parser.add_argument("--output-dir", type=Path, default=FIELD_DATASET_DIR)
    parser.add_argument("--export-dir", action="append", type=Path)
    args = parser.parse_args()
    result = build_yolo_dataset(mode=args.mode, output_dir=args.output_dir, export_roots=args.export_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    if result["status"].startswith("DATASET_BUILD_SKIPPED"):
        return 0 if args.mode == "dry-run" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
