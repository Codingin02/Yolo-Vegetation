from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.ngrok_runtime_probe import probe_ngrok_runtime  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Progress 5.3 ngrok runtime probe without token usage.")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args(argv)
    result = probe_ngrok_runtime(port=args.port)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "NGROK_HTTPS_TUNNEL_READY":
        print("NGROK_HTTPS_TUNNEL_READY")
        print(result["field_capture_public_url"])
    else:
        print(f"{result['status']}: {result['operator_command']}")
        print(f"NGROK_NOT_RUNNING_RUN: ngrok http {args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
