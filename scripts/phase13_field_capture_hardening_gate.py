from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from ulp_project.flask_app import create_app
    from ulp_project import phase9_monitoring

    app = create_app()
    client = app.test_client()
    checks: dict[str, object] = {}

    field = client.get("/field-capture")
    checks["field_capture_200"] = field.status_code == 200
    html = field.get_data(as_text=True)
    checks["secure_context_diagnostic"] = "HTTP_LAN" in html and "HTTPS_SECURE" in html
    checks["no_mobile_app_wording"] = "APK" not in html and "Flutter" not in html and "React Native" not in html

    for endpoint in ["/api/network/whoami", "/api/latency/ping"]:
        response = client.get(endpoint)
        checks[f"{endpoint}_200_json"] = response.status_code == 200 and response.content_type.startswith("application/json")

    original_append = phase9_monitoring._append_row_to_csv

    def locked_writer(*args, **kwargs):
        raise PermissionError("simulated csv lock")

    phase9_monitoring._append_row_to_csv = locked_writer
    try:
        locked = client.post(
            "/api/field-capture/upload",
            json={"point_id": "phase13_lock", "clearance_m": 0.3, "growth_rate_m_per_day": 0.01},
        )
        locked_json = locked.get_json() or {}
        checks["upload_csv_locked_json"] = locked.status_code == 200 and locked.content_type.startswith("application/json")
        checks["csv_lock_fallback"] = locked_json.get("report_status") in {"REPORT_WRITTEN_SPOOL_CSV_LOCKED", "REPORT_WRITE_FAILED"}
    finally:
        phase9_monitoring._append_row_to_csv = original_append

    payload = {"point_id": "phase13_dedup", "clearance_m": 0.3, "growth_rate_m_per_day": 0.01, "capture_fingerprint": "phase13_gate_same"}
    first = client.post("/api/field-capture/upload", json=payload).get_json() or {}
    second = client.post("/api/field-capture/upload", json=payload).get_json() or {}
    checks["duplicate_coalesced"] = first.get("request_dedup_status") == "ACCEPTED_NEW" and second.get("request_dedup_status") == "DUPLICATE_COOLESCED"

    js = (ROOT / "src" / "ulp_project" / "static" / "field_capture.js").read_text(encoding="utf-8")
    checks["frontend_non_json_guard"] = "API_ERROR_NON_JSON_RESPONSE" in js and "content-type" in js

    forbidden_suffixes = {".apk", ".aab"}
    forbidden_hits = []
    for root in ["src", "scripts", "docs", "tests", "configs"]:
        for path in (ROOT / root).rglob("*"):
            if path.is_file() and path.suffix.lower() in forbidden_suffixes:
                forbidden_hits.append(str(path.relative_to(ROOT)))
    checks["no_apk_artifacts"] = not forbidden_hits
    checks["forbidden_hits"] = forbidden_hits

    passed = all(value is True for key, value in checks.items() if key != "forbidden_hits")
    status = "PHASE13_FIELD_CAPTURE_HARDENED_READY" if passed else "PHASE13_FIELD_CAPTURE_HARDENING_FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2, ensure_ascii=False))
    print(status)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
