from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from phase5_2_report_map_smoke import build_smoke_status as build_phase5_2_report_map_smoke  # noqa: E402
from ulp_project.flask_app import create_app  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        app = create_app(runtime_root=Path(tmpdir))
        client = app.test_client()
        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        required_routes = {
            "/field-capture",
            "/field-trial-checklist",
            "/api/runtime/tunnel-status",
            "/api/field-trial/hp-result",
            "/api/field-trial/evidence",
            "/api/operator/failure-recovery",
        }
        field_html = client.get("/field-capture").get_data(as_text=True)
        checklist_html = client.get("/field-trial-checklist").get_data(as_text=True)
        tunnel = client.get("/api/runtime/tunnel-status").get_json()
        failure = client.post(
            "/api/operator/failure-recovery",
            json={"url_attempted": "http://localhost:5000/field-capture", "hp_can_open_url": False},
        ).get_json()
        hp_result = client.post(
            "/api/field-trial/hp-result",
            json={
                "network_type": "unknown",
                "public_url_opened": True,
                "server_connection_ok": True,
                "camera_ok": True,
                "gps_ok": False,
                "manual_prediction_ok": True,
                "snapshot_report_ok": True,
                "map_report_ok": True,
                "notes": "Laptop smoke only.",
            },
        ).get_json()
        evidence = client.get("/api/field-trial/evidence?dry_run=1").get_json()
        manual = client.post(
            "/api/field/manual-prediction",
            json={"point_id": "V001_pohon_sono", "clearance_m": 5.0, "growth_rate_m_per_day": 0.01},
        ).get_json()
        report_map = build_phase5_2_report_map_smoke()
        checks = {
            "new_routes_present": required_routes.issubset(routes),
            "field_capture_kept_progress5_2": "manual-prediction" in field_html and "snapshot-report" in field_html,
            "field_capture_has_recovery_panel": "Failure Recovery Help" in field_html and "Open Field Trial Checklist" in field_html,
            "checklist_page_ready": "HP membuka URL public tunnel" in checklist_html and "Simpan Hasil Uji HP" in checklist_html,
            "tunnel_probe_endpoint_honest": tunnel.get("status")
            in {"NGROK_HTTPS_TUNNEL_READY", "NGROK_RUNNING_NO_HTTPS_TUNNEL", "PUBLIC_TUNNEL_NOT_RUNNING", "NGROK_CLI_FOUND_BUT_TUNNEL_NOT_RUNNING", "NGROK_NOT_RUNNING"},
            "failure_recovery_endpoint_ready": failure.get("status") == "FAILURE_RECOVERY_DECISION_READY",
            "hp_result_intake_ready": hp_result.get("status") == "HP_RESULT_RECORDED",
            "evidence_dry_run_ready": evidence.get("status") == "FIELD_TRIAL_EVIDENCE_READY" and evidence.get("evidence_written") is False,
            "manual_prediction_still_uses_3m_threshold": manual.get("eta_days") == 200.0,
            "report_map_smoke_pass": report_map.get("status") == "PHASE5_2_REPORT_MAP_SMOKE_PASS",
        }
    passed = all(checks.values())
    return {
        "status": "PROGRESS5_3_ACTUAL_RUNTIME_SMOKE_PASS" if passed else "PROGRESS5_3_ACTUAL_RUNTIME_SMOKE_FAIL",
        "checks": checks,
        "tunnel_status": tunnel.get("status"),
        "hp_physical_test_status": "HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION",
    }


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
