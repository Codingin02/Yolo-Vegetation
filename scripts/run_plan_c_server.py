from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app  # noqa: E402

REQUIRED_ROUTES = {
    "/plan-c",
    "/api/plan-c/session/start",
    "/api/plan-c/session/snapshot",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Plan C single-class server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()

    app = create_app()
    registered = {rule.rule for rule in app.url_map.iter_rules()}
    missing = sorted(REQUIRED_ROUTES - registered)
    if missing:
        print("PLAN_C_ROUTE_NOT_REGISTERED")
        print("missing_routes=" + ",".join(missing))
        return 1

    with app.test_client() as client:
        response = client.get("/plan-c")
        if response.status_code != 200:
            print("PLAN_C_ROUTE_NOT_REGISTERED")
            print(f"/plan-c status={response.status_code}")
            return 1

    print("PLAN C server starting")
    print(f"Local URL: http://127.0.0.1:{args.port}/plan-c")
    print("HP tunnel URL format: https://<ngrok-url>/plan-c")
    print("Runtime: PLAN_C_SINGLE_CLASS_POHON_SONO")
    print("Detector: YOLOv8 single-class")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
