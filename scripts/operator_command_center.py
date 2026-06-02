from __future__ import annotations

import argparse


COMMAND_GROUPS = {
    "SAFE NOW": [
        ".\\venv\\Scripts\\python.exe scripts\\system_status_report.py",
        ".\\venv\\Scripts\\python.exe scripts\\phase8_pln_realtime_risk_gate.py",
        ".\\venv\\Scripts\\python.exe scripts\\run_field_capture_server.py",
        "Open browser: http://<IP-LAPTOP>:5000/field-capture",
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


def render_command_center() -> str:
    lines = ["ULP Project Operator Command Center", "Set-Location E:\\Projects\\ULP_Project", ""]
    for group, commands in COMMAND_GROUPS.items():
        lines.append(group)
        for command in commands:
            lines.append(f"  {command}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe ULP operator commands.")
    parser.add_argument("--dry-run", action="store_true")
    parser.parse_args()
    print(render_command_center())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
