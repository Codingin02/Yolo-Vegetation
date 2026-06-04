from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from progress5_4_camera_ui_contract_smoke import build_smoke_status as build_camera_contract  # noqa: E402
from progress5_4_favicon_smoke import build_smoke_status as build_favicon  # noqa: E402
from progress5_4_geometry_math_smoke import build_smoke_status as build_geometry  # noqa: E402
from progress5_4_map_public_link_smoke import build_smoke_status as build_map  # noqa: E402
from progress5_4_public_tunnel_smoke import build_smoke_status as build_public_tunnel  # noqa: E402
from progress5_4_runtime_status_tunnel_sync_smoke import build_smoke_status as build_tunnel_sync  # noqa: E402
from progress5_4_shutter_autosave_smoke import build_smoke_status as build_shutter  # noqa: E402
from ulp_project.model_handoff import check_model_handoff  # noqa: E402


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
    public_tunnel = build_public_tunnel()
    camera = build_camera_contract()
    shutter = build_shutter()
    tunnel_sync = build_tunnel_sync()
    favicon = build_favicon()
    map_status = build_map()
    geometry = build_geometry()
    model = check_model_handoff()
    checks = {
        "public_https_workflow_schema": public_tunnel["status"] == "PROGRESS5_4_PUBLIC_TUNNEL_SMOKE_PASS",
        "camera_gps_ui_contract": camera["status"] == "PROGRESS5_4_CAMERA_UI_CONTRACT_SMOKE_PASS",
        "shutter_autosave": shutter["status"] == "PROGRESS5_4_SHUTTER_AUTOSAVE_SMOKE_PASS",
        "runtime_tunnel_sync": tunnel_sync["status"] == "PROGRESS5_4_RUNTIME_STATUS_TUNNEL_SYNC_SMOKE_PASS",
        "favicon_no_500": favicon["status"] == "PROGRESS5_4_FAVICON_SMOKE_PASS",
        "map_public_link": map_status["status"] == "PROGRESS5_4_MAP_PUBLIC_LINK_SMOKE_PASS",
        "geometry_core": geometry["status"] == "PROGRESS5_4_GEOMETRY_MATH_SMOKE_PASS",
        "no_label_touch": _no_forbidden_git_touch(),
        "model_not_ready_is_safe": model["model_status"] == "MODEL_NOT_READY" or str(model["model_status"]).startswith("MODEL_PRESENT"),
    }
    if not all(checks.values()):
        status = "PROGRESS_5_4_BLOCKED_REMOTE_HTTPS_GATE_CHECK_FAILED"
    elif model["model_status"] == "MODEL_NOT_READY":
        status = "PROGRESS_5_4_REMOTE_HTTPS_CAMERA_GPS_YOLO_SHUTTER_READY_MODEL_NOT_READY_SAFE_MODE"
    else:
        status = "PROGRESS_5_4_REMOTE_HTTPS_CAMERA_GPS_YOLO_SHUTTER_READY_WITH_REAL_MODEL"
    return {
        "status": status,
        "checks": checks,
        "model_status": model["model_status"],
        "public_tunnel_status": public_tunnel.get("links", {}).get("tunnel_status"),
        "public_field_capture_url": public_tunnel.get("public_field_capture_url"),
        "debug_coco_status": "DEBUG_COCO_YOLO_NOT_FIELD_MODEL_EXPLICIT_ONLY",
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
