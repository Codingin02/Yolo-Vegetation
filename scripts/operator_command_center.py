from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


COMMAND_GROUPS = {
    "SAFE NOW": [
        ".\\venv\\Scripts\\python.exe scripts\\system_status_report.py",
        ".\\venv\\Scripts\\python.exe scripts\\diagnose_field_capture_deploy.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase10_lan_deploy_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase8_pln_realtime_risk_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\run_field_capture_server.py --host 0.0.0.0 --port 5000",
        "Open browser: http://<IP-LAPTOP>:5000/field-capture",
        ".\\venv\\Scripts\\python.exe scripts\\phase9_rough_realtime_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase11_provisional_eta_demo.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase12_end_to_end_rough_demo.py",
        ".\\venv\\Scripts\\python.exe scripts\\print_secure_capture_options.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase13_field_capture_hardening_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase14_auto_yolo_measurement_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase15_realtime_eta_system_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase15_rough_realtime_auto_demo.py --mode mock-auto",
        ".\\venv\\Scripts\\python.exe scripts\\print_remote_realtime_links.py",
        ".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000",
        ".\\venv\\Scripts\\python.exe scripts\\phase16_remote_realtime_streaming_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\run_realtime_field_pipeline.py --mode all-dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\phase12_calibration_readiness_check.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase12_environmental_readiness_check.py",
        ".\\venv\\Scripts\\python.exe scripts\\export_vegetation_risk_report.py --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\export_vegetation_risk_map.py --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\run_manual_risk_estimate.py --sample pohon_sono --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\run_realtime_field_pipeline.py --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\run_system_runtime.py --mode all-dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\fetch_environmental_data.py --point V001_pohon_sono --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\build_environmental_features.py --point V001_pohon_sono --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\run_vegetation_risk.py --point V001_pohon_sono --mode sample-risk",
        ".\\venv\\Scripts\\python.exe scripts\\run_flask_dev.py",
        ".\\venv\\Scripts\\python.exe scripts\\build_system_map.py --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\export_system_report.py --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\run_inference_runtime.py --mode image --input sample.jpg",
        ".\\venv\\Scripts\\python.exe scripts\\phase5_2_ui_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase5_2_prediction_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase5_2_report_map_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase5_2_field_trial_prediction_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_3_ngrok_probe.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_3_actual_runtime_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_3_evidence_pack.py --dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_3_field_trial_execution_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_camera_ui_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_geometry_math_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_shutter_report_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_realtime_yolo_geometry_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_public_tunnel_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_camera_ui_contract_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_shutter_autosave_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_runtime_status_tunnel_sync_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_favicon_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_map_public_link_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_remote_https_camera_yolo_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_prepare_labeling_handoff.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_label_export_validator.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_build_yolo_dataset.py --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_train_yolov8_initial.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_integrate_bestpt_runtime.py --write-example",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_labeling_training_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_2_makesense_export_to_training_gate.py --write-reports",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_2_dataset_build_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_2_training_policy_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_2_bestpt_runtime_handoff_smoke.py",
    ],
    "WAIT UNTIL MAKESENSE EXPORT": [
        ".\\venv\\Scripts\\python.exe scripts\\phase3_readiness_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase4_integration_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy",
        ".\\venv\\Scripts\\python.exe scripts\\validate_yolo_labels.py --point V001_pohon_sono",
    ],
    "WAIT UNTIL LABEL VALIDATION": [
        ".\\venv\\Scripts\\python.exe scripts\\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166",
        ".\\venv\\Scripts\\python.exe scripts\\build_field_multiclass_dataset.py --mode build --val-ratio 0.2 --seed 23050874166",
        ".\\venv\\Scripts\\python.exe scripts\\generate_data_yaml.py --mode write",
        ".\\venv\\Scripts\\python.exe scripts\\train_yolov8_field_multiclass.py --dry-run",
    ],
    "WAIT UNTIL EXPLICIT TRAINING APPROVAL": [
        ".\\venv\\Scripts\\python.exe scripts\\train_yolov8_field_multiclass.py --run --model yolov8n.pt --epochs 50 --imgsz 640 --batch auto --device 0",
    ],
}

MODE_GROUPS = {
    "phase10-deploy": [
        ".\\venv\\Scripts\\python.exe scripts\\diagnose_field_capture_deploy.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase10_lan_deploy_smoke.py",
    ],
    "field-capture-server": [
        ".\\venv\\Scripts\\python.exe scripts\\run_field_capture_server.py --host 0.0.0.0 --port 5000",
        "Open HP browser: http://<IP-LAPTOP>:5000/field-capture",
    ],
    "rough-smoke": [
        ".\\venv\\Scripts\\python.exe scripts\\phase10_lan_deploy_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase11_provisional_eta_demo.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase12_end_to_end_rough_demo.py",
    ],
    "phase12-status": [
        ".\\venv\\Scripts\\python.exe scripts\\run_realtime_field_pipeline.py --mode status",
        ".\\venv\\Scripts\\python.exe scripts\\phase12_calibration_readiness_check.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase12_environmental_readiness_check.py",
    ],
    "phase12-demo": [".\\venv\\Scripts\\python.exe scripts\\phase12_end_to_end_rough_demo.py"],
    "phase12-export-report": [".\\venv\\Scripts\\python.exe scripts\\export_google_sheets_ready_csv.py --mode dry-run"],
    "phase12-export-map": [".\\venv\\Scripts\\python.exe scripts\\export_vegetation_risk_map.py --mode dry-run"],
    "phase12-calibration-check": [".\\venv\\Scripts\\python.exe scripts\\phase12_calibration_readiness_check.py"],
    "phase12-environment-check": [".\\venv\\Scripts\\python.exe scripts\\phase12_environmental_readiness_check.py"],
    "phase14-auto-measurement": [".\\venv\\Scripts\\python.exe scripts\\phase14_auto_yolo_measurement_gate.py"],
    "phase15-eta-system": [
        ".\\venv\\Scripts\\python.exe scripts\\phase15_realtime_eta_system_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase15_rough_realtime_auto_demo.py --mode mock-auto",
    ],
    "phase16-remote-realtime": [
        ".\\venv\\Scripts\\python.exe scripts\\print_remote_realtime_links.py",
        ".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000",
        ".\\venv\\Scripts\\python.exe scripts\\phase16_remote_realtime_streaming_gate.py",
    ],
    "phase5-2-field-trial": [
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --diagnose",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --print-links",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --check-model",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --field-trial-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --phase5-2-gate",
    ],
    "progress5-3-field-trial": [
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --diagnose",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --print-links",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --ngrok-probe",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --actual-runtime-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --evidence-pack",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --progress5-3-gate",
        ".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000",
        "Tunnel: ngrok http 5000",
        "HP: https://<ngrok-public-url>/field-capture",
        "HP checklist: https://<ngrok-public-url>/field-trial-checklist",
    ],
    "progress5-4-camera-geometry": [
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --public-tunnel-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --camera-ui-contract-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --geometry-math-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --shutter-autosave-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --runtime-tunnel-sync-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --favicon-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --map-public-link-smoke",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --progress5-4-gate",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --realtime-camera-server",
        "Tunnel: ngrok http 5000",
        "HP: https://<ngrok-public-url>/field-capture",
    ],
    "progress6-1-labeling-training": [
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_remote_https_camera_yolo_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_prepare_labeling_handoff.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_label_export_validator.py --write-reports",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_build_yolo_dataset.py --mode dry-run",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_train_yolov8_initial.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_check_trained_model.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_integrate_bestpt_runtime.py --write-example",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_labeling_training_gate.py",
    ],
    "progress6-2-makesense-training": [
        ".\\venv\\Scripts\\python.exe scripts\\progress5_4_remote_https_camera_yolo_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_labeling_training_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_1_label_export_validator.py --write-reports",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_2_makesense_export_to_training_gate.py --write-reports",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_2_dataset_build_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_2_training_policy_smoke.py",
        ".\\venv\\Scripts\\python.exe scripts\\progress6_2_bestpt_runtime_handoff_smoke.py",
    ],
}


def render_command_center(mode: str = "all") -> str:
    lines = ["ULP Project Operator Command Center", "Set-Location E:\\Projects\\ULP_Project", ""]
    if mode != "all":
        lines.append(mode)
        for command in MODE_GROUPS.get(mode, []):
            lines.append(f"  {command}")
        return "\n".join(lines)
    for group, commands in COMMAND_GROUPS.items():
        lines.append(group)
        for command in commands:
            lines.append(f"  {command}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe ULP operator commands.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--print-links", action="store_true")
    parser.add_argument("--run-server", action="store_true")
    parser.add_argument("--run-remote-server", action="store_true")
    parser.add_argument("--check-model", action="store_true")
    parser.add_argument("--check-calibration", action="store_true")
    parser.add_argument("--check-environment", action="store_true")
    parser.add_argument("--export-report", action="store_true")
    parser.add_argument("--export-map", action="store_true")
    parser.add_argument("--field-trial-dry-run", action="store_true")
    parser.add_argument("--field-trial-start", action="store_true")
    parser.add_argument("--field-trial-smoke", action="store_true")
    parser.add_argument("--ui-smoke", action="store_true")
    parser.add_argument("--prediction-smoke", action="store_true")
    parser.add_argument("--report-smoke", action="store_true")
    parser.add_argument("--map-smoke", action="store_true")
    parser.add_argument("--remote-security-check", action="store_true")
    parser.add_argument("--phase5-2-gate", action="store_true")
    parser.add_argument("--progress5-3-gate", action="store_true")
    parser.add_argument("--actual-runtime-smoke", action="store_true")
    parser.add_argument("--ngrok-probe", action="store_true")
    parser.add_argument("--evidence-pack", action="store_true")
    parser.add_argument("--hp-result-intake-smoke", action="store_true")
    parser.add_argument("--failure-recovery-smoke", action="store_true")
    parser.add_argument("--print-field-trial-checklist", action="store_true")
    parser.add_argument("--progress5-4-gate", action="store_true")
    parser.add_argument("--camera-ui-smoke", action="store_true")
    parser.add_argument("--shutter-report-smoke", action="store_true")
    parser.add_argument("--geometry-math-smoke", action="store_true")
    parser.add_argument("--public-tunnel-smoke", action="store_true")
    parser.add_argument("--camera-ui-contract-smoke", action="store_true")
    parser.add_argument("--shutter-autosave-smoke", action="store_true")
    parser.add_argument("--runtime-tunnel-sync-smoke", action="store_true")
    parser.add_argument("--favicon-smoke", action="store_true")
    parser.add_argument("--map-public-link-smoke", action="store_true")
    parser.add_argument("--print-public-field-url", action="store_true")
    parser.add_argument("--realtime-camera-server", action="store_true")
    parser.add_argument("--print-progress5-4-commands", action="store_true")
    parser.add_argument("--progress6-1-gate", action="store_true")
    parser.add_argument("--prepare-labeling-handoff", action="store_true")
    parser.add_argument("--label-export-validator", action="store_true")
    parser.add_argument("--build-yolo-dataset-dry-run", action="store_true")
    parser.add_argument("--train-yolov8-initial-dry-run", action="store_true")
    parser.add_argument("--check-trained-model", action="store_true")
    parser.add_argument("--integrate-bestpt-runtime", action="store_true")
    parser.add_argument("--progress6-2-gate", action="store_true")
    parser.add_argument("--progress6-2-dataset-build-smoke", action="store_true")
    parser.add_argument("--progress6-2-training-policy-smoke", action="store_true")
    parser.add_argument("--progress6-2-bestpt-handoff-smoke", action="store_true")
    parser.add_argument("--all-gates", action="store_true")
    parser.add_argument("--mode", choices=["all", *MODE_GROUPS.keys()], default="all")
    args = parser.parse_args()
    actions = [
        (args.status, ["scripts\\system_status_report.py"]),
        (args.diagnose, ["scripts\\diagnose_remote_field_trial.py"]),
        (args.print_links, ["scripts\\print_remote_realtime_links.py"]),
        (args.run_server, ["scripts\\run_field_capture_server.py", "--host", "0.0.0.0", "--port", "5000"]),
        (args.run_remote_server, ["scripts\\run_remote_realtime_server.py", "--host", "0.0.0.0", "--port", "5000"]),
        (args.check_model, ["scripts\\check_model_handoff_ready.py"]),
        (args.check_calibration, ["scripts\\phase18_calibration_gate.py"]),
        (args.check_environment, ["scripts\\phase18_environmental_gate.py"]),
        (args.export_report, ["scripts\\export_google_sheets_ready_csv.py", "--mode", "local"]),
        (args.export_map, ["scripts\\export_latest_risk_map.py"]),
        (args.field_trial_dry_run, ["scripts\\run_field_trial_operator.py", "--mode", "dry-run"]),
        (args.field_trial_start, ["scripts\\run_remote_realtime_server.py", "--host", "0.0.0.0", "--port", "5000"]),
        (args.field_trial_smoke, ["scripts\\phase5_2_field_trial_prediction_gate.py"]),
        (args.ui_smoke, ["scripts\\phase5_2_ui_smoke.py"]),
        (args.prediction_smoke, ["scripts\\phase5_2_prediction_smoke.py"]),
        (args.report_smoke, ["scripts\\phase5_2_report_map_smoke.py", "--report-only"]),
        (args.map_smoke, ["scripts\\phase5_2_report_map_smoke.py", "--map-only"]),
        (args.remote_security_check, ["scripts\\phase5_2_field_trial_prediction_gate.py", "--security-only"]),
        (args.phase5_2_gate, ["scripts\\phase5_2_field_trial_prediction_gate.py"]),
        (args.progress5_3_gate, ["scripts\\progress5_3_field_trial_execution_gate.py"]),
        (args.actual_runtime_smoke, ["scripts\\progress5_3_actual_runtime_smoke.py"]),
        (args.ngrok_probe, ["scripts\\progress5_3_ngrok_probe.py"]),
        (args.evidence_pack, ["scripts\\progress5_3_evidence_pack.py"]),
        (args.hp_result_intake_smoke, ["scripts\\progress5_3_hp_result_intake.py"]),
        (args.failure_recovery_smoke, ["scripts\\progress5_3_failure_recovery_smoke.py"]),
        (args.print_field_trial_checklist, ["scripts\\progress5_3_print_field_trial_checklist.py"]),
        (args.progress5_4_gate, ["scripts\\progress5_4_remote_https_camera_yolo_gate.py"]),
        (args.camera_ui_smoke, ["scripts\\progress5_4_camera_ui_smoke.py"]),
        (args.shutter_report_smoke, ["scripts\\progress5_4_shutter_report_smoke.py"]),
        (args.geometry_math_smoke, ["scripts\\progress5_4_geometry_math_smoke.py"]),
        (args.public_tunnel_smoke, ["scripts\\progress5_4_public_tunnel_smoke.py"]),
        (args.camera_ui_contract_smoke, ["scripts\\progress5_4_camera_ui_contract_smoke.py"]),
        (args.shutter_autosave_smoke, ["scripts\\progress5_4_shutter_autosave_smoke.py"]),
        (args.runtime_tunnel_sync_smoke, ["scripts\\progress5_4_runtime_status_tunnel_sync_smoke.py"]),
        (args.favicon_smoke, ["scripts\\progress5_4_favicon_smoke.py"]),
        (args.map_public_link_smoke, ["scripts\\progress5_4_map_public_link_smoke.py"]),
        (args.print_public_field_url, ["scripts\\progress5_4_public_tunnel_smoke.py"]),
        (args.realtime_camera_server, ["scripts\\run_remote_realtime_server.py", "--host", "0.0.0.0", "--port", "5000"]),
        (args.print_progress5_4_commands, ["scripts\\progress5_4_print_commands.py"]),
        (args.progress6_1_gate, ["scripts\\progress6_1_labeling_training_gate.py"]),
        (args.prepare_labeling_handoff, ["scripts\\progress6_1_prepare_labeling_handoff.py"]),
        (args.label_export_validator, ["scripts\\progress6_1_label_export_validator.py"]),
        (args.build_yolo_dataset_dry_run, ["scripts\\progress6_1_build_yolo_dataset.py", "--mode", "dry-run"]),
        (args.train_yolov8_initial_dry_run, ["scripts\\progress6_1_train_yolov8_initial.py"]),
        (args.check_trained_model, ["scripts\\progress6_1_check_trained_model.py"]),
        (args.integrate_bestpt_runtime, ["scripts\\progress6_1_integrate_bestpt_runtime.py", "--write-example"]),
        (args.progress6_2_gate, ["scripts\\progress6_2_makesense_export_to_training_gate.py", "--write-reports"]),
        (args.progress6_2_dataset_build_smoke, ["scripts\\progress6_2_dataset_build_smoke.py"]),
        (args.progress6_2_training_policy_smoke, ["scripts\\progress6_2_training_policy_smoke.py"]),
        (args.progress6_2_bestpt_handoff_smoke, ["scripts\\progress6_2_bestpt_runtime_handoff_smoke.py"]),
        (args.all_gates, ["scripts\\phase17_20_final_system_completion_gate.py"]),
    ]
    selected = [cmd for enabled, cmd in actions if enabled]
    if selected:
        for cmd in selected:
            print(f"> .\\venv\\Scripts\\python.exe {' '.join(cmd)}")
            completed = subprocess.run([sys.executable, *cmd], cwd=ROOT, check=False)
            if completed.returncode != 0:
                return completed.returncode
        return 0
    print(render_command_center(args.mode))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
