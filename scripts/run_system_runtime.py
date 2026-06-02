from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.pipeline_orchestrator import VALID_MODES, run_pipeline_mode  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 5 system runtime modes safely.")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="status")
    args = parser.parse_args(argv)
    result = run_pipeline_mode(args.mode, ROOT)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
