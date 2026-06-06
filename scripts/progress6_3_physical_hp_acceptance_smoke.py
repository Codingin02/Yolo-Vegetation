from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app


def run_smoke() -> dict[str, object]:
    with TemporaryDirectory() as tmp:
        app = create_app(runtime_root=Path(tmp))
        client = app.test_client()
        page = client.get("/field-acceptance")
        start = client.post(
            "/api/field/acceptance/start",
            json={
                "session_id": "SMOKE_ACCEPTANCE",
                "current_url_mode": "HTTPS_PUBLIC_READY",
                "secure_context_status": "SECURE_CONTEXT_OK",
            },
        )
        status = client.get("/api/field/acceptance/status")
        latest = client.get("/api/field/acceptance/latest")
        evidence = client.get("/api/field/acceptance/evidence")
        ok = all(response.status_code < 400 for response in [page, start, status, latest, evidence])
        latest_json = latest.get_json() or {}
        pending = latest_json.get("acceptance_status") == "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"
        return {
            "status": "PROGRESS_6_3_ACCEPTANCE_SMOKE_PASS" if ok and pending else "PROGRESS_6_3_ACCEPTANCE_SMOKE_FAILED",
            "page_status_code": page.status_code,
            "start_status_code": start.status_code,
            "latest_acceptance_status": latest_json.get("acceptance_status"),
            "physical_pass_not_faked": pending,
        }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PROGRESS_6_3_ACCEPTANCE_SMOKE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
