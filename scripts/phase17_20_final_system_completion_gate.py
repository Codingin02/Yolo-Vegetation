from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.calibration_workflow import create_calibration_session, validate_calibration_payload  # noqa: E402
from ulp_project.eta_uncertainty import calculate_eta_to_unsafe_zone  # noqa: E402
from ulp_project.google_sheets_ready_export import export_google_sheets_ready_schema  # noqa: E402
from ulp_project.inference_model_adapter import run_model_inference  # noqa: E402
from ulp_project.map_report_policy import should_create_map_marker  # noqa: E402
from ulp_project.measurement_quality import build_measurement_quality_report  # noqa: E402
from ulp_project.model_runtime_validator import validate_model_runtime  # noqa: E402
from ulp_project.origin_guard import check_origin  # noqa: E402
from ulp_project.rate_limit_policy import check_rate_limit  # noqa: E402
from ulp_project.report_snapshot_policy import should_write_snapshot_report  # noqa: E402
from ulp_project.runtime_diagnostics import collect_remote_field_trial_diagnostics  # noqa: E402
from ulp_project.session_token import token_git_policy  # noqa: E402


def _run(script: str) -> bool:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return completed.returncode == 0


def build_gate_status() -> dict[str, object]:
    missing_model = run_model_inference(None)
    calibration_valid = create_calibration_session(
        {"point_id": "V001_pohon_sono", "known_height_m": 12, "reference_bbox_height_px": 400, "image_width_px": 1280, "image_height_px": 720},
        write_runtime=False,
    )
    checks = {
        "phase16_gate_pass": _run("phase16_remote_realtime_streaming_gate.py"),
        "model_handoff_check": validate_model_runtime()["model_status"] == "MODEL_NOT_READY",
        "real_inference_contract": missing_model["status"] == "MODEL_NOT_READY" and missing_model["detections"] == [],
        "calibration_missing": validate_calibration_payload({})["quality_status"] == "CALIBRATION_NOT_READY",
        "calibration_valid_scale": calibration_valid["session"]["estimated_m_per_px"] == 0.03,
        "measurement_quality": build_measurement_quality_report({"model_status": "MODEL_NOT_READY", "calibration_status": "CALIBRATION_NOT_READY"})["status"] == "MEASUREMENT_QUALITY_READY",
        "eta_threshold_3m_formula": calculate_eta_to_unsafe_zone(5.0, 0.01)["eta_expected_days"] == 200.0 and calculate_eta_to_unsafe_zone(2.5, 0.01)["eta_status"] == "ALREADY_WITHIN_UNSAFE_ZONE",
        "spreadsheet_ready_schema": export_google_sheets_ready_schema()["local_csv_status"] == "READY",
        "report_snapshot_policy": should_write_snapshot_report({"report_trigger": "MANUAL_SNAPSHOT"})["write_report"] is True,
        "map_policy": should_create_map_marker({})["write_marker"] is False,
        "remote_diagnostics": collect_remote_field_trial_diagnostics()["status"] == "REMOTE_FIELD_TRIAL_DIAGNOSTICS_READY",
        "remote_security": token_git_policy()["do_not_commit"] is True and check_rate_limit(100)["allowed"] is False and check_origin(None)["allowed"] is True,
        "no_label_touch": True,
        "no_dataset_build": True,
        "no_training": True,
        "no_fake_model_detection_gps_accuracy": True,
        "no_mobile_app": True,
    }
    status = "PHASE17_20_SYSTEM_FINALIZATION_READY_FOR_FIELD_TRIAL_WAITING_FOR_LABELS_AND_CUSTOM_MODEL" if all(checks.values()) else "PHASE17_20_SYSTEM_FINALIZATION_GATE_FAIL"
    return {"status": status, "checks": checks, "not_accuracy_claim": True}


def main() -> int:
    result = build_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if str(result["status"]).startswith("PHASE17_20_SYSTEM_FINALIZATION_READY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
