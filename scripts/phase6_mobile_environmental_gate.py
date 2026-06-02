from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.environmental_sources import environmental_source_status, load_environmental_source_config  # noqa: E402
from ulp_project.system_status import collect_project_status  # noqa: E402


def _git(args: list[str], root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _flask_status() -> dict[str, Any]:
    try:
        from ulp_project.flask_app import create_app
    except Exception as exc:  # pragma: no cover
        return {"status": "FLASK_IMPORT_NOT_READY", "error": str(exc)}
    try:
        app = create_app()
    except RuntimeError as exc:
        return {"status": "FLASK_NOT_INSTALLED", "error": str(exc)}
    client = app.test_client()
    health = client.get("/health")
    network = client.get("/api/mobile/network/status")
    mobile = client.get("/mobile")
    return {
        "status": "FLASK_ENDPOINTS_READY" if health.status_code == 200 and network.status_code == 200 and mobile.status_code == 200 else "FLASK_ENDPOINTS_PARTIAL",
        "health_code": health.status_code,
        "network_code": network.status_code,
        "mobile_code": mobile.status_code,
    }


def build_phase6_gate_status(project_root: Path = ROOT) -> dict[str, Any]:
    status = collect_project_status(project_root)
    env_config = load_environmental_source_config(project_root / "configs" / "surabaya_perak_environment.yaml")
    env_status = environmental_source_status(env_config)
    flask_status = _flask_status()
    model_status = status["model"]["status"]
    dataset_status = status["field_dataset"]["status"]
    labeling_status = status["labels_selected"]["status"]
    field_capture = status.get("field_capture", {})
    tunnel_config_exists = (project_root / "configs" / "runtime_network.yaml").exists()
    map_report_ready = bool(
        (project_root / "src" / "ulp_project" / "map_runtime.py").exists()
        and (project_root / "src" / "ulp_project" / "report_export.py").exists()
    )
    if model_status != "MODEL_READY" or labeling_status != "LABELS_READY":
        overall_status = "PHASE6_SYSTEM_READY_WAITING_FOR_LABELS_AND_MODEL"
    else:
        overall_status = "PHASE6_READY_FOR_OPERATOR_REVIEW"
    return {
        "branch": _git(["branch", "--show-current"], project_root),
        "commit": _git(["rev-parse", "--short", "HEAD"], project_root),
        "model_status": model_status,
        "dataset_status": dataset_status,
        "labeling_status": labeling_status,
        "environmental_source_status": env_status["status"],
        "field_capture_status": field_capture.get("status", "FIELD_CAPTURE_NOT_READY"),
        "tunnel_config_status": "TUNNEL_CONFIG_READY_ENV_ONLY" if tunnel_config_exists else "TUNNEL_CONFIG_NOT_READY",
        "flask_endpoint_status": flask_status["status"],
        "map_report_status": "MAP_REPORT_READY_FOR_DRY_RUN" if map_report_ready else "MAP_REPORT_NOT_READY",
        "overall_status": overall_status,
        "details": {
            "images_selected_count": status["images_selected"]["image_count"],
            "labels_selected_count": status["labels_selected"]["label_count"],
            "mobile_page_exists": field_capture.get("field_capture_page_exists", False),
            "secret_policy": "env_only",
        },
    }


def main() -> int:
    result = build_phase6_gate_status(ROOT)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["overall_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
