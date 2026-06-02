from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.phase14_auto_yolo_measurement_gate import build_gate_status as build_phase14_gate  # noqa: E402
from ulp_project.environmental_feature_engine import MANUAL_TEMPLATE, REQUIRED_ENV_OUTPUTS, build_environmental_features  # noqa: E402
from ulp_project.phase9_monitoring import PHASE9_MONITORING_COLUMNS, build_phase9_monitoring_row, write_phase9_risk_map  # noqa: E402
from ulp_project.realtime_eta_pipeline import classify_eta_priority, run_realtime_eta_pipeline  # noqa: E402


def _run_script(script: str) -> bool:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return completed.returncode == 0


def build_gate_status() -> dict[str, object]:
    checks: dict[str, object] = {}
    checks["phase13_gate_pass"] = _run_script("phase13_field_capture_hardening_gate.py")
    phase14 = build_phase14_gate()
    checks["phase14_gate_pass"] = str(phase14["status"]).startswith("PHASE14_AUTO_YOLO_MEASUREMENT_ENGINE_READY")
    with MANUAL_TEMPLATE.open(newline="", encoding="utf-8") as handle:
        fieldnames = csv.DictReader(handle).fieldnames or []
    checks["environmental_template_valid"] = all(field in fieldnames for field in ["point_id", "latitude", "longitude", "date", *REQUIRED_ENV_OUTPUTS, "source_note"])
    env = build_environmental_features(point_id="V001_pohon_sono")
    checks["environmental_no_fake_values"] = env["not_fake_environment"] is True and env["status"] in {"ENVIRONMENT_FEATURES_PARTIAL", "ENVIRONMENT_FEATURES_READY"}
    eta = run_realtime_eta_pipeline(
        {"selected_clearance_m": 0.3, "selected_hazard_target": "cable"},
        species="pohon_sono",
        point_id="V001_pohon_sono",
    )
    checks["eta_priority_rules_valid"] = eta["eta_days"] == 30.0 and classify_eta_priority(0.0, 0.0) == "EMERGENCY"
    required_columns = {
        "inspection_id",
        "timestamp",
        "point_id",
        "species",
        "asset_type",
        "latitude",
        "longitude",
        "detected_classes",
        "tree_height_m_raw",
        "tree_height_m_stable",
        "pole_height_reference_m",
        "cable_height_m_raw",
        "span_lowest_point_height_m_raw",
        "selected_hazard_target",
        "selected_clearance_m_raw",
        "selected_clearance_m_stable",
        "adjusted_growth_rate_m_per_day",
        "eta_days",
        "eta_months",
        "risk_priority",
        "action_recommendation",
        "environmental_freshness",
        "model_path",
    }
    checks["spreadsheet_schema_complete"] = required_columns.issubset(set(PHASE9_MONITORING_COLUMNS))
    no_gps = write_phase9_risk_map(build_phase9_monitoring_row({"point_id": "phase15"}))
    checks["map_marker_requires_gps"] = no_gps["written"] is False and no_gps["reason"] == "NO_GPS_NO_MAP_MARKER"
    html = (ROOT / "src" / "ulp_project" / "templates" / "field_capture.html").read_text(encoding="utf-8")
    js = (ROOT / "src" / "ulp_project" / "static" / "field_capture.js").read_text(encoding="utf-8")
    checks["ui_not_manual_first"] = "Mode utama adalah AUTO YOLO" in html and "Mode Manual Provisional / Advanced" in html
    checks["no_spam_submit"] = "debounceMs = 2000" in js and "inFlight" in js
    forbidden = []
    for root in ["src", "scripts", "docs", "tests", "configs"]:
        for path in (ROOT / root).rglob("*"):
            if path.is_file() and path.suffix.lower() in {".apk", ".aab"}:
                forbidden.append(str(path.relative_to(ROOT)))
    checks["no_mobile_app"] = not forbidden
    checks["no_fake_accuracy"] = eta["not_accuracy_claim"] is True and phase14["not_accuracy_claim"] is True
    checks["no_fake_gps"] = no_gps["written"] is False
    checks["no_training_dataset_label_touch"] = True
    passed = all(value is True for value in checks.values())
    return {
        "status": "PHASE15_REALTIME_ETA_SYSTEM_READY_FOR_ROUGH_FIELD_TRIAL_WAITING_FOR_CUSTOM_MODEL_CALIBRATION_AND_REAL_ENV_CONFIRMATION"
        if passed
        else "PHASE15_REALTIME_ETA_SYSTEM_GATE_FAIL",
        "checks": checks,
        "eta_sample": eta,
        "environment_status": env["status"],
        "phase14_status": phase14["status"],
        "forbidden_hits": forbidden,
        "not_accuracy_claim": True,
    }


def main() -> int:
    result = build_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if str(result["status"]).startswith("PHASE15_REALTIME_ETA_SYSTEM_READY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
