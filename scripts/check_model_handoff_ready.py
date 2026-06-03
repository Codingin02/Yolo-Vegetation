from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.model_runtime_validator import validate_model_runtime  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check custom YOLO model handoff readiness without training.")
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--dry-load", action="store_true")
    args = parser.parse_args(argv)
    result = validate_model_runtime(args.model_path, dry_load=args.dry_load)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["model_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
