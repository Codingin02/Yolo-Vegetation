from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from progress5_4_camera_ui_smoke import build_smoke_status as build_camera_ui_smoke  # noqa: E402
from progress5_4_geometry_math_smoke import build_smoke_status as build_geometry_smoke  # noqa: E402
from progress5_4_shutter_report_smoke import build_smoke_status as build_shutter_smoke  # noqa: E402
from ulp_project.environment import build_environment_status  # noqa: E402
from ulp_project.model_handoff import check_model_handoff  # noqa: E402
from ulp_project.progress5_4_field_runtime import progress5_4_realtime_status  # noqa: E402


FORBIDDEN_PREFIXES = (
    "data/dataset_yolo/",
    "data/raw/",
    "data/gps/",
    "data/processed/",
    "data/exports/",
    "dataset_botol/",
    "results/",
    "runs/",
    "models/",
    "weights/",
)


def build_gate_status() -> dict[str, object]:
    camera = build_camera_ui_smoke()
    geometry = build_geometry_smoke()
    shutter = build_shutter_smoke()
    model = check_model_handoff()
    runtime = progress5_4_realtime_status()
    environment = build_environment_status()
    checks = {
        "camera_ui_smoke": camera["status"] == "PROGRESS5_4_CAMERA_UI_SMOKE_PASS",
        "geometry_math_smoke": geometry["status"] == "PROGRESS5_4_GEOMETRY_MATH_SMOKE_PASS",
        "shutter_report_smoke": shutter["status"] == "PROGRESS5_4_SHUTTER_REPORT_SMOKE_PASS",
        "gps_background_ready": camera["checks"]["gps_background_watch_position"],
        "no_fake_detection_safe_mode": runtime["no_fake_detection"] is True,
        "environment_no_fabrication": environment["no_fabricated_environment_data"] is True,
        "no_forbidden_git_touch": _no_forbidden_git_touch(),
    }
    passed = all(checks.values())
    if not passed:
        status = "PROGRESS_5_4_BLOCKED_GATE_CHECK_FAILED"
    elif model["model_status"] == "MODEL_NOT_READY":
        status = "PROGRESS_5_4_REALTIME_CAMERA_GEOMETRY_READY_MODEL_NOT_READY_SAFE_MODE"
    else:
        status = "PROGRESS_5_4_REALTIME_CAMERA_GEOMETRY_READY_WITH_REAL_MODEL"
    return {
        "status": status,
        "checks": checks,
        "model_status": model["model_status"],
        "debug_coco_status": "DEBUG_COCO_YOLO_OPTIONAL_EXPLICIT_NOT_FIELD_MODEL",
        "hp_physical_display_test": "HP_PHYSICAL_DISPLAY_TEST_PENDING",
        "environment_status": environment["environment_status"],
    }


def _no_forbidden_git_touch() -> bool:
    completed = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        return False
    for line in completed.stdout.splitlines():
        path = line[3:].replace("\\", "/")
        if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            return False
    return True


def main() -> int:
    result = build_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if "READY" in result["status"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
