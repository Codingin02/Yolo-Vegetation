from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress6_1_labeling import FIELD_DATASET_DIR, training_plan  # noqa: E402


def _cuda_status() -> dict[str, object]:
    try:
        import torch
    except ImportError:
        return {"cuda_available": False, "device": "TORCH_NOT_INSTALLED"}
    available = bool(torch.cuda.is_available())
    return {"cuda_available": available, "device": torch.cuda.get_device_name(0) if available else "CPU"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe YOLOv8 initial training launcher. Dry-run by default.")
    parser.add_argument("--data", type=Path, default=FIELD_DATASET_DIR / "data.yaml")
    parser.add_argument("--run", action="store_true", help="Actually run training command after readiness checks.")
    parser.add_argument("--cpu-smoke", action="store_true", help="Force CPU smoke command planning.")
    args = parser.parse_args()
    cuda = _cuda_status()
    plan = training_plan(data_yaml=args.data, cuda_available=False if args.cpu_smoke else bool(cuda["cuda_available"]))
    plan["cuda"] = cuda
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    print(plan["status"])
    if not args.run:
        return 0
    if not args.data.exists():
        return 1
    completed = subprocess.run(plan["command"], cwd=ROOT, shell=True, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
