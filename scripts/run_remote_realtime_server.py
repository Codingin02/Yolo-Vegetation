from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from print_remote_realtime_links import build_remote_link_help  # noqa: E402
from ulp_project.flask_app import create_app  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ULP Phase 16 remote realtime field capture server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args(argv)
    print("ULP Phase 16 remote realtime server starting")
    print(build_remote_link_help(args.port))
    print("")
    print("Realtime endpoints:")
    print("  GET  /field-capture")
    print("  GET  /api/realtime/session/new")
    print("  POST /api/realtime/frame")
    print("  POST /api/realtime/report-snapshot")
    print("  WS   /ws/realtime-detect")
    print("")
    app = create_app()
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
