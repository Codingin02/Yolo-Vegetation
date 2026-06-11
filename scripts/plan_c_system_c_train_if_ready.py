"""Train System C YOLOv8 only when the dataset gate is ready."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ulp_project.plan_c_system_c_train_yolov8 import train_if_ready  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Train System C YOLOv8 if gate passes")
    parser.add_argument("--dry-run", action="store_true", help="Check readiness without starting training.")
    args = parser.parse_args()
    result = train_if_ready(allow_training=not args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
