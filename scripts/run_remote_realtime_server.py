from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from print_remote_realtime_links import build_remote_link_help  # noqa: E402
from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.runtime_links import format_startup_links  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ULP Phase 16 remote realtime field capture server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--public-url", default="", help="Optional runtime HTTPS tunnel URL. Do not commit this value.")
    args = parser.parse_args(argv)
    print(format_startup_links(host=args.host, port=args.port, public_url=args.public_url))
    print("")
    print(build_remote_link_help(args.port))
    print("")
    print("Realtime endpoints:")
    print("  GET  /field-capture")
    print("  GET  /api/runtime/public-links")
    print("  GET  /api/runtime/status")
    print("  GET  /api/runtime/route-registry")
    print("  GET  /api/runtime/yolo-readiness")
    print("  GET  /api/model/status")
    print("  GET  /api/calibration/status")
    print("  GET  /field-camera")
    print("  GET  /field-map/session/<session_id>")
    print("  GET  /field-spreadsheet/session/<session_id>")
    print("  POST /api/field/session/start")
    print("  POST /api/field/session/frame")
    print("  POST /api/field/session/gps-update")
    print("  POST /api/field/session/shutter")
    print("  GET  /api/realtime/session/new")
    print("  POST /api/realtime/frame")
    print("  POST /api/field/manual-prediction")
    print("  POST /api/field/snapshot-report")
    print("  POST /api/realtime/report-snapshot")
    print("  WS   /ws/realtime-detect")
    print("")
    app = create_app()
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
