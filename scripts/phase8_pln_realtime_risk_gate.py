from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.risk_map_exporter import export_risk_map  # noqa: E402
from ulp_project.risk_priority import evaluate_pln_vegetation_risk  # noqa: E402
from ulp_project.spreadsheet_schema import PHASE8_SPREADSHEET_COLUMNS  # noqa: E402
from ulp_project.system_status import collect_project_status  # noqa: E402


FORBIDDEN_IMPLEMENTATION_TERMS = ["flutter", "react native", ".apk", ".aab"]


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
        "field_capture": client.get("/field-capture").status_code,
        "mobile_alias": client.get("/mobile").status_code,
        "latency": client.get("/api/latency/ping").status_code,
    }
    ok = checks["field_capture"] == 200 and checks["mobile_alias"] in {301, 302} and checks["latency"] == 200
    return {"status": "FIELD_CAPTURE_BROWSER_READY" if ok else "FIELD_CAPTURE_BROWSER_NOT_READY", "checks": checks}


def _source_forbidden_terms() -> dict[str, object]:
    hits: list[str] = []
    for root in [ROOT / "src", ROOT / "scripts", ROOT / "docs", ROOT / "tests", ROOT / "configs"]:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for term in FORBIDDEN_IMPLEMENTATION_TERMS:
                if term in text and "tidak membuat" not in text and "tidak ada" not in text and "not make" not in text and "not in" not in text:
                    hits.append(str(path.relative_to(ROOT)))
    return {"status": "NO_MOBILE_APP_FRAMEWORK_IMPLEMENTATION" if not hits else "FORBIDDEN_TERMS_FOUND", "hits": hits}


def build_phase8_gate_status() -> dict[str, object]:
    project = collect_project_status(ROOT)
    manual_complete = evaluate_pln_vegetation_risk(
        0.3,
        "pohon_sono",
        environment={"season_label": "manual", "rainfall_30d_mm": 100, "soil_ph": 6.5, "soil_moisture_proxy": "manual"},
        allow_provisional=True,
        base_growth_rate_override=0.01,
    )
    insufficient = evaluate_pln_vegetation_risk(None, "pohon_sono")
    map_check = export_risk_map([{"point_id": "V001_pohon_sono"}], mode="dry-run")
    schema_ready = all(column in PHASE8_SPREADSHEET_COLUMNS for column in ["timestamp", "point_id", "minimum_clearance_m", "days_to_contact_p50", "risk_priority"])
    status = {
        "branch": _git(["branch", "--show-current"]),
        "commit": _git(["rev-parse", "--short", "HEAD"]),
        "field_capture_route": _route_status(),
        "no_mobile_app_framework": _source_forbidden_terms(),
        "spreadsheet_schema_status": "SPREADSHEET_SCHEMA_READY" if schema_ready else "SPREADSHEET_SCHEMA_INCOMPLETE",
        "manual_eta_status": manual_complete["eta_status"],
        "manual_eta_days_p50": manual_complete["days_to_contact_p50"],
        "manual_risk_priority": manual_complete["risk_priority"],
        "insufficient_data_status": insufficient["risk_priority"],
        "map_without_gps_status": "NO_MARKER_WITHOUT_GPS" if map_check["features"] == 0 and map_check["gps_missing"] == 1 else "MAP_GPS_RULE_FAILED",
        "labeling_status": project["labels_selected"]["status"],
        "model_status": project["model"]["status"],
        "dataset_status": project["field_dataset"]["status"],
        "overall_status": "PHASE8_PLN_REALTIME_RISK_SYSTEM_READY_WAITING_FOR_MODEL_LABELS_AND_REAL_ENV_DATA",
    }
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return status


def main() -> int:
    status = build_phase8_gate_status()
    print(status["overall_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
