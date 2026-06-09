from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\Projects\ULP_Project")
SRC = ROOT / "src"
REPORT = ROOT / "reports" / "progress7_start_contract_no_gps_test.json"

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
    app = load_app()
    client = app.test_client()

    start_payload = {
        "point_id": "PROGRESS7_NO_GPS_CONTRACT",
        "operator_note": "system-first start without GPS",
        "source": "progress7_start_contract_no_gps_test"
    }

    start = client.post("/api/field/session/start", json=start_payload)
    data = start.get_json(silent=True) or {}

    session_id = data.get("session_id") or ""
    camera_url = data.get("camera_url") or ""

    result = {
        "status": "UNKNOWN",
        "http_status": start.status_code,
        "session_id": session_id,
        "camera_url": camera_url,
        "start_response": data,
        "checks": {
            "http_201": start.status_code == 201,
            "session_id_present": bool(session_id),
            "camera_url_present": bool(camera_url),
            "camera_url_contains_session": bool(session_id and session_id in camera_url),
            "not_gps_pending_block": data.get("status") != "FIELD_SESSION_START_READY_GPS_PENDING",
            "recording_active_or_started": data.get("recording_status") in ("RECORDING_ACTIVE", "RECORDING_STARTED") or data.get("status") == "FIELD_SESSION_STARTED",
            "model_status_not_unknown": "UNKNOWN" not in str(data),
        }
    }

    hard_failures = [k for k, v in result["checks"].items() if not v]
    result["hard_failures"] = hard_failures

    if hard_failures:
        result["status"] = "PROGRESS7_START_CONTRACT_NO_GPS_FAILED"
        code = 1
    else:
        result["status"] = "PROGRESS7_START_CONTRACT_NO_GPS_PASS"
        code = 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
