from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        app = create_app(runtime_root=Path(tmpdir))
        client = app.test_client()
        response = client.post(
            "/api/field-trial/hp-result",
            json={
                "operator_name": "SMOKE_ONLY",
                "device_name": "browser-test-client",
                "browser_name": "flask-test-client",
                "network_type": "unknown",
                "public_url_opened": True,
                "server_connection_ok": True,
                "camera_ok": True,
                "gps_ok": False,
                "manual_prediction_ok": True,
                "snapshot_report_ok": True,
                "map_report_ok": True,
                "error_code": "GPS_NOT_TESTED_BY_LAPTOP_SMOKE",
                "notes": "Smoke test does not prove physical HP success.",
                "screenshot_base64": "SHOULD_NOT_BE_STORED",
            },
        )
        payload = response.get_json()
        result_path = Path(payload.get("path", ""))
        checks = {
            "endpoint_created": response.status_code == 201,
            "runtime_path_used": str(result_path).startswith(str(Path(tmpdir))),
            "hp_result_recorded": payload.get("status") == "HP_RESULT_RECORDED",
            "hp_confirmed_for_synthetic_intake": payload.get("hp_physical_confirmation_status") == "HP_CONFIRMED",
            "screenshot_not_stored": "screenshot_base64" not in payload and payload.get("no_screenshot_stored") is True,
        }
    passed = all(checks.values())
    return {
        "status": "PROGRESS5_3_HP_RESULT_INTAKE_SMOKE_PASS" if passed else "PROGRESS5_3_HP_RESULT_INTAKE_SMOKE_FAIL",
        "checks": checks,
    }


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
