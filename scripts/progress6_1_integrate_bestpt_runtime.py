from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_1_labeling import DEFAULT_MODEL_CANDIDATE, PROJECT_ROOT, integrate_bestpt_runtime, write_local_model_runtime_example  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check best.pt runtime path registration without copying weights.")
    parser.add_argument("--model", type=Path, default=PROJECT_ROOT / DEFAULT_MODEL_CANDIDATE)
    parser.add_argument("--write-example", action="store_true")
    args = parser.parse_args()
    if args.write_example:
        write_local_model_runtime_example()
    result = integrate_bestpt_runtime(args.model)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"] == "BESTPT_RUNTIME_PATH_REGISTERED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
