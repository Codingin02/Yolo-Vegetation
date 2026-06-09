import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

SCRIPTS = [
    "scripts/progress6_26_yolo_first_backend_smoke.py",
    "scripts/progress6_26_frontend_switch_contract_smoke.py",
    "scripts/progress6_26_shutter_evidence_only_smoke.py",
    "scripts/progress6_26_project_class_filter_smoke.py",
    "scripts/progress6_26_prediction_panel_contract_smoke.py",
    "scripts/progress6_26_icon_status_contract_smoke.py",
    "scripts/progress6_26_dataset_source_audit.py",
]

def run(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout

def main():
    results = []
    for script in SCRIPTS:
        out = run([PY, script])
        results.append({"script": script, "status": "PASS"})
    print(json.dumps({
        "status": "PROGRESS_6_26_YOLO_FIRST_HYBRID_REALTIME_DETECTION_AND_PREDICTION_RUNTIME_PASS",
        "core_realtime_endpoint": "/api/field/session/frame",
        "vision_analyze_core_loop": False,
        "shutter_evidence_only": True,
        "no_fake_detection": True,
        "no_label_touch": True,
        "results": results,
    }, indent=2))

if __name__ == "__main__":
    main()
