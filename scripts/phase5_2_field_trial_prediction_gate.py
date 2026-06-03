from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.origin_guard import check_origin  # noqa: E402
from ulp_project.phase5_2_field_trial import build_manual_prediction  # noqa: E402
from ulp_project.rate_limit_policy import check_rate_limit  # noqa: E402
from ulp_project.realtime_streaming import create_realtime_session, process_realtime_frame  # noqa: E402
from ulp_project.runtime_links import build_public_links  # noqa: E402
from ulp_project.session_token import token_git_policy  # noqa: E402


FORBIDDEN_PREFIXES = (
    "data/dataset_yolo/00_review_candidates/",
    "data/exports/",
    "data/raw/",
    "data/gps/",
    "data/processed/",
    "data/dataset_yolo/field_multiclass_v1/",
    "dataset_botol/",
    "results/",
    "runs/",
    "weights/",
    "models/",
)


def _run_script(script: str, *args: str) -> bool:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return completed.returncode == 0


def _git_status_lines() -> list[str]:
    completed = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return completed.stdout.splitlines()


def _no_forbidden_git_touch() -> bool:
    for line in _git_status_lines():
        path = line[3:].replace("\\", "/")
        if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            return False
    return True


def _realtime_payload(session: dict[str, object], frame_id: str, image_base64: str = "") -> dict[str, object]:
    return {
        "session_id": session["session_id"],
        "session_token": session["session_token"],
        "frame_id": frame_id,
        "timestamp_client_ms": int(time.time() * 1000),
        "point_id": "V001_pohon_sono",
        "species_hint": "pohon_sono",
        "asset_type": "span",
        "gps_lat": "",
        "gps_lon": "",
        "image_jpeg_base64": image_base64,
        "client_mode": "remote_https",
        "requested_interval_ms": 1000,
    }


def build_gate_status(*, security_only: bool = False) -> dict[str, object]:
    app = create_app()
    client = app.test_client()
    links = build_public_links(5000)
    manual = build_manual_prediction({"point_id": "V001_pohon_sono", "clearance_m": 5.0, "growth_rate_m_per_day": 0.01})
    unsafe = build_manual_prediction({"point_id": "V001_pohon_sono", "clearance_m": 2.75, "growth_rate_m_per_day": 0.01})
    session = create_realtime_session(ROOT / "data" / "runtime")
    frame = process_realtime_frame(_realtime_payload(session, "p52_frame"))
    large_session = create_realtime_session(ROOT / "data" / "runtime")
    large_frame = process_realtime_frame(_realtime_payload(large_session, "p52_large", base64.b64encode(b"x" * 1_500_001).decode("ascii")))

    security_checks = {
        "token_runtime_policy": token_git_policy()["do_not_commit"] is True,
        "rate_limit_guard": check_rate_limit(100)["allowed"] is False,
        "origin_guard": check_origin(None)["allowed"] is True,
        "frame_size_guard": large_frame["status"] == "FRAME_TOO_LARGE_DROPPED",
        "base64_not_returned": large_frame.get("image_jpeg_base64") is None and large_frame.get("overlay_image_jpeg_base64") is None,
        "runtime_outputs_ignored": "outputs/*" in (ROOT / ".gitignore").read_text(encoding="utf-8") and "data/runtime/" in (ROOT / ".gitignore").read_text(encoding="utf-8"),
    }
    if security_only:
        checks = security_checks
    else:
        checks = {
            "ui_smoke": _run_script("phase5_2_ui_smoke.py"),
            "prediction_smoke": _run_script("phase5_2_prediction_smoke.py"),
            "report_map_smoke": _run_script("phase5_2_report_map_smoke.py"),
            "route_field_capture": client.get("/field-capture").status_code == 200,
            "runtime_public_links": links["status"] in {"READY", "NO_PUBLIC_TUNNEL_CONFIGURED"},
            "runtime_public_links_endpoint": client.get("/api/runtime/public-links").status_code == 200,
            "model_status_endpoint": client.get("/api/model/status").status_code == 200,
            "calibration_status_endpoint": client.get("/api/calibration/status").status_code == 200,
            "manual_prediction_endpoint": client.post("/api/field/manual-prediction", json={"clearance_m": 5.0, "growth_rate_m_per_day": 0.01}).status_code == 200,
            "snapshot_report_endpoint": client.post("/api/field/snapshot-report", json={"clearance_m": 5.0, "growth_rate_m_per_day": 0.01}).status_code in {200, 202},
            "no_model_safe_mode": manual["model_status"] == "MODEL_NOT_READY" and manual["detections"] == [],
            "manual_eta_threshold_3m": manual["eta_days"] == 200.0,
            "unsafe_clearance_policy": unsafe["eta_days"] == 0 and unsafe["clearance_display_m_integer_floor"] == 2 and unsafe["action_priority"] == "CRITICAL",
            "report_not_every_frame": "report_written" not in frame and "report_status" not in frame,
            "no_forbidden_git_touch": _no_forbidden_git_touch(),
            "no_mobile_app_artifacts": not list((ROOT / "src").rglob("*.apk")) and not list((ROOT / "src").rglob("*.aab")),
            **security_checks,
        }
    passed = all(checks.values())
    model_status = manual["model_status"]
    ready_status = (
        "PROGRESS_5_2_FIELD_TRIAL_PREDICTION_WEB_RUNTIME_READY_WITH_MODEL_NOT_READY_SAFE_MODE"
        if model_status == "MODEL_NOT_READY"
        else "PROGRESS_5_2_FIELD_TRIAL_PREDICTION_WEB_RUNTIME_READY_WITH_REAL_MODEL"
    )
    return {
        "status": ready_status if passed else "PROGRESS_5_2_FIELD_TRIAL_PREDICTION_GATE_FAIL",
        "checks": checks,
        "model_status": model_status,
        "manual_prediction": manual,
        "unsafe_prediction": unsafe,
        "public_links": links,
        "not_accuracy_claim": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Progress 5.2 field trial prediction web runtime gate.")
    parser.add_argument("--security-only", action="store_true")
    args = parser.parse_args(argv)
    result = build_gate_status(security_only=args.security_only)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if str(result["status"]).startswith("PROGRESS_5_2_FIELD_TRIAL_PREDICTION_WEB_RUNTIME_READY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
