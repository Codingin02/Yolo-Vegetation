import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app

app = create_app()
routes = sorted(str(rule.rule) for rule in app.url_map.iter_rules())

required = [
    "/api/runtime/progress6-22-vision-status",
    "/api/field/session/vision-analyze",
]

report = {
    "status": "PROGRESS_6_22_IMPORT_ROUTE_SMOKE_PASS",
    "src_path_added": str(SRC),
    "required": {path: path in routes for path in required},
    "route_count": len(routes),
}

if not all(report["required"].values()):
    report["status"] = "PROGRESS_6_22_IMPORT_ROUTE_SMOKE_FAILED"

print(json.dumps(report, indent=2, ensure_ascii=False))

if report["status"] != "PROGRESS_6_22_IMPORT_ROUTE_SMOKE_PASS":
    raise SystemExit(report["status"])
