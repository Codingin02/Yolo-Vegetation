"""Register a System C model only after explicit validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ulp_project.plan_c_system_c_model_registry import register_model_if_valid  # noqa: E402
from ulp_project.plan_c_system_c_training_gate import run_training_gate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Register System C YOLO model if valid")
    parser.add_argument("--model-path", default="", help="Path to trained .pt model.")
    args = parser.parse_args()
    gate = run_training_gate()
    if not args.model_path:
        result = {"status": "MODEL_REGISTRY_SKIPPED_MODEL_PATH_NOT_PROVIDED", "gate": gate, "runtime_allowed": False}
    else:
        result = register_model_if_valid(model_path=args.model_path, gate_status=str(gate.get("status") or ""))
        result["gate"] = gate
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
