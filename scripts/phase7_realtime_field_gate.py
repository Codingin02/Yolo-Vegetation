from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.sheets_report_schema import REPORT_COLUMNS  # noqa: E402
from ulp_project.system_status import collect_project_status  # noqa: E402
from ulp_project.time_to_contact import estimate_time_to_contact  # noqa: E402
from ulp_project.vegetation_clearance import classify_operational_risk  # noqa: E402


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _route_status() -> dict[str, object]:
    try:
        app = create_app()
    except RuntimeError as exc:
        return {"status": "FLASK_NOT_READY", "error": str(exc)}
    client = app.test_client()
    checks = {
        "/field-capture": client.get("/field-capture").status_code,
        "/mobile": client.get("/mobile").status_code,
        "/api/field-capture/ping": client.get("/api/field-capture/ping").status_code,
        "/operator": client.get("/operator").status_code,
    }
    ok = checks["/field-capture"] == 200 and checks["/mobile"] in {301, 302} and checks["/api/field-capture/ping"] == 200
    return {"status": "FIELD_CAPTURE_ROUTES_READY" if ok else "FIELD_CAPTURE_ROUTES_PARTIAL", "checks": checks}


def build_phase7_gate_status() -> dict[str, object]:
    status = collect_project_status(ROOT)
    route = _route_status()
    eta = estimate_time_to_contact(None, {})
    report_schema_ready = len(REPORT_COLUMNS) >= 40
    overall = "PHASE7_READY_WAITING_FOR_LABELS_MODEL_CALIBRATION_ENVIRONMENT"
    return {
        "branch": _git(["branch", "--show-current"]),
        "commit": _git(["rev-parse", "--short", "HEAD"]),
        "labeling_status": status["labels_selected"]["status"],
        "model_status": status["model"]["status"],
        "dataset_status": status["field_dataset"]["status"],
        "field_capture_status": route["status"],
        "operator_dashboard_status": "OPERATOR_DASHBOARD_READY",
        "report_schema_status": "REPORT_SCHEMA_READY" if report_schema_ready else "REPORT_SCHEMA_INCOMPLETE",
        "risk_engine_status": classify_operational_risk(None),
        "eta_prediction_status": eta["status"],
        "calibration_status": "CALIBRATION_NOT_READY",
        "environmental_data_status": status["environmental_data"]["status"],
        "overall_status": overall,
        "not_accuracy_claim": True,
        "route_details": route,
    }


def main() -> int:
    result = build_phase7_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["overall_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
