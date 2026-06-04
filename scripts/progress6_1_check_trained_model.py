from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_1_labeling import DEFAULT_MODEL_CANDIDATE, PROJECT_ROOT, check_trained_model  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check best.pt candidate without committing model weights.")
    parser.add_argument("--model", type=Path, default=PROJECT_ROOT / DEFAULT_MODEL_CANDIDATE)
    args = parser.parse_args()
    result = check_trained_model(args.model)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"] in {"BESTPT_NOT_FOUND", "MODEL_LOAD_CANDIDATE_READY_CLASS_ORDER_UNVERIFIED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
