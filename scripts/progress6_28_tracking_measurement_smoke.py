from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(r"E:\Projects\ULP_Project")
SRC = ROOT / "src"
REPORT = ROOT / "reports" / "progress6_28_tracking_measurement_smoke.json"

sys.path.insert(0, str(SRC))


def load_app():
    mod = importlib.import_module("ulp_project.flask_app")
    if hasattr(mod, "create_app"):
        return mod.create_app()
    if hasattr(mod, "app"):
        return mod.app
    if hasattr(mod, "get_app"):
        return mod.get_app()
    raise RuntimeError("APP_FACTORY_NOT_FOUND")


def main() -> int:
    from ulp_project.progress6_28_tracking_measurement_runtime import (
        make_synthetic_frame_base64,
        process_frame_payload,
    )

    result: Dict[str, Any] = {
        "version": "progress6_28_tracking_measurement_smoke",
        "status": "UNKNOWN",
        "hard_failures": [],
        "local_runtime_checks": {},
        "flask_route_checks": {},
        "safety": {
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
        },
    }

    frame1 = make_synthetic_frame_base64(offset_x=0)
    frame2 = make_synthetic_frame_base64(offset_x=6)

    payload1 = {
        "session_id": "FS_PROGRESS6_28_SMOKE",
        "frame_base64": frame1,
        "synthetic_smoke": True,
    }
    payload2 = {
        "session_id": "FS_PROGRESS6_28_SMOKE",
        "frame_base64": frame2,
        "synthetic_smoke": True,
    }

    r1 = process_frame_payload(payload1)
    r2 = process_frame_payload(payload2)

    result["local_runtime_checks"]["frame1"] = r1
    result["local_runtime_checks"]["frame2"] = r2

    t1 = r1.get("tracking", {}).get("tracked_detections", [])
    t2 = r2.get("tracking", {}).get("tracked_detections", [])

    if not r1.get("ok") or not r2.get("ok"):
        result["hard_failures"].append("LOCAL_RUNTIME_NOT_OK")

    if not t1 or not t2:
        result["hard_failures"].append("SYNTHETIC_TRACKING_NO_DETECTIONS")

    if t1 and t2:
        id1 = t1[0].get("track_id")
        id2 = t2[0].get("track_id")
        result["local_runtime_checks"]["track_id_stability"] = {
            "id1": id1,
            "id2": id2,
            "stable": id1 == id2,
        }
        if id1 != id2:
            result["hard_failures"].append("TRACK_ID_FLICKER_ON_SYNTHETIC_FRAMES")

    if r2.get("measurement", {}).get("clearance_status") not in {
        "CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR",
        "CLEARANCE_NOT_FINAL",
    }:
        result["hard_failures"].append("CLEARANCE_GUARD_NOT_SAFE")

    if r2.get("eta_status") not in {None, "ETA_NOT_FINAL"}:
        result["hard_failures"].append("ETA_GUARD_NOT_SAFE")

    app = load_app()
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    route = "/api/field/session/progress6-28-diagnostic-frame"
    result["flask_route_checks"]["route_present"] = route in routes

    if route not in routes:
        result["hard_failures"].append("PROGRESS6_28_ROUTE_NOT_REGISTERED")
    else:
        client = app.test_client()
        resp = client.post(route, json=payload1)
        result["flask_route_checks"]["http_status"] = resp.status_code
        data = resp.get_json(silent=True)
        result["flask_route_checks"]["response"] = data
        if resp.status_code in (404, 405, 500):
            result["hard_failures"].append(f"PROGRESS6_28_ROUTE_BAD_HTTP:{resp.status_code}")
        if not isinstance(data, dict) or data.get("ok") is not True:
            result["hard_failures"].append("PROGRESS6_28_ROUTE_RESPONSE_NOT_OK")

    if result["hard_failures"]:
        result["status"] = "PROGRESS_6_28_TRACKING_MEASUREMENT_SMOKE_FAILED"
        code = 1
    else:
        result["status"] = "PROGRESS_6_28_TRACKING_MEASUREMENT_SMOKE_PASS"
        code = 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
