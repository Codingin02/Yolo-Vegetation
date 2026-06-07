from __future__ import annotations

import base64
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def run_smoke() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        client = create_app(runtime_root=Path(tmp)).test_client()
        start = client.post(
            "/api/field/session/start",
            json={
                "point_id": "V001_pohon_sono",
                "camera_status": "CAMERA_READY",
                "base_latitude": -7.2161234,
                "base_longitude": 112.7351234,
                "base_accuracy_m": 3.8,
                "source_mode": "SMOKE_TEST",
                "idempotency_key": "P67_FRAME_START",
            },
        ).get_json()
        session_id = start.get("session_id")
        image = "data:image/png;base64," + base64.b64encode(PNG_1X1).decode("ascii")
        cases = {
            "valid_or_model_safe": {"session_id": session_id, "frame_image_base64": image},
            "invalid_base64": {"session_id": session_id, "frame_image_base64": "%%%bad"},
            "empty_image": {"session_id": session_id},
            "missing_session": {"frame_image_base64": image},
        }
        results = {}
        for name, payload in cases.items():
            response = client.post("/api/field/session/frame", json=payload)
            body = response.get_json() or {}
            results[name] = {"status_code": response.status_code, "status": body.get("status"), "model_status": body.get("model_status")}
        checks = {
            "start_has_session_id": bool(session_id),
            "valid_frame_no_500": results["valid_or_model_safe"]["status_code"] != 500,
            "invalid_base64_no_500": results["invalid_base64"]["status_code"] != 500
            and results["invalid_base64"]["status"] == "FRAME_DECODE_FAILED_SAFE",
            "empty_image_no_500": results["empty_image"]["status_code"] != 500
            and results["empty_image"]["status"] == "FRAME_SKIPPED_NO_IMAGE",
            "missing_session_400_json": results["missing_session"]["status_code"] == 400
            and results["missing_session"]["status"] == "FIELD_SESSION_ID_REQUIRED",
        }
    return {
        "status": "PROGRESS_6_7_LIVE_FRAME_NO_500_PASS" if all(checks.values()) else "PROGRESS_6_7_LIVE_FRAME_NO_500_FAIL",
        "checks": checks,
        "results": results,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
