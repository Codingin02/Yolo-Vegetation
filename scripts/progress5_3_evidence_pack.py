from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.field_trial_evidence import build_field_trial_evidence_pack  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Progress 5.3 field-trial evidence pack generator.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args(argv)
    result = build_field_trial_evidence_pack(port=args.port, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    if result.get("hp_physical_confirmation_status") != "HP_CONFIRMED":
        print("HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION")
    if result.get("ngrok_status") != "NGROK_HTTPS_TUNNEL_READY":
        print("PUBLIC_TUNNEL_NOT_RUNNING")
        print(f"NGROK_NOT_RUNNING_RUN: ngrok http {args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
