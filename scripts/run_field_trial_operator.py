from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.runtime_diagnostics import collect_remote_field_trial_diagnostics  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Field trial operator facade.")
    parser.add_argument("--mode", choices=["dry-run", "server", "smoke"], default="dry-run")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args(argv)
    if args.mode == "server":
        return subprocess.call([sys.executable, str(ROOT / "scripts" / "run_remote_realtime_server.py"), "--host", args.host, "--port", str(args.port)], cwd=ROOT)
    if args.mode == "smoke":
        return subprocess.call([sys.executable, str(ROOT / "scripts" / "phase5_2_field_trial_prediction_gate.py")], cwd=ROOT)
    result = collect_remote_field_trial_diagnostics(args.port)
    result["field_trial_status"] = "FIELD_TRIAL_DRY_RUN_READY_WAITING_FOR_MODEL_CALIBRATION_AND_LABELS"
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["field_trial_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
