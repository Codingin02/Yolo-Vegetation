from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vegetation_monitoring.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the vegetation monitoring server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--dev", action="store_true", help="Use the Flask development server.")
    args = parser.parse_args()
    app = create_app()
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    if "/vegetation" not in routes or "/api/vegetation/realtime/frame" not in routes:
        raise SystemExit("VEGETATION_ROUTE_NOT_REGISTERED")
    print(f"Sistem Monitoring Vegetasi: http://{args.host}:{args.port}/vegetation")
    if args.dev:
        app.run(host=args.host, port=args.port, debug=False, threaded=True)
        return
    from waitress import serve

    serve(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
