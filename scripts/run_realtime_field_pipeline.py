from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.google_sheets_export import export_google_sheets_ready_csv  # noqa: E402
from ulp_project.phase9_monitoring import MONITORING_CSV, RISK_MAP_HTML, build_phase9_monitoring_row, write_phase9_risk_map  # noqa: E402
from ulp_project.realtime_field_pipeline import pipeline_status, process_realtime_inspection  # noqa: E402


def _demo_payload(with_gps: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "inspection_id": "DEMO_SAMPLE_NOT_FIELD_DATA",
        "point_id": "V001_pohon_sono_demo",
        "species": "pohon_sono",
        "asset_type": "span",
        "clearance_m": 0.30,
        "growth_rate_m_per_day": 0.01,
        "measurement_source": "manual",
        "confidence_status": "PROVISIONAL",
        "notes": "DEMO_SAMPLE_NOT_FIELD_DATA",
    }
    if with_gps:
        payload.update({"latitude": "-7.000000", "longitude": "112.000000"})
    return payload


def _run_server(host: str, port: int) -> int:
    command = [sys.executable, str(ROOT / "scripts" / "run_field_capture_server.py"), "--host", host, "--port", str(port)]
    return subprocess.call(command, cwd=ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unified rough realtime PLN vegetation monitoring pipeline.")
    parser.add_argument("--mode", choices=["server", "demo-submit", "export-report", "export-map", "all-dry-run", "status"], default="status")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--with-sample-gps", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "server":
        return _run_server(args.host, args.port)
    if args.mode == "status":
        print(json.dumps({**pipeline_status(), "report_csv": str(MONITORING_CSV), "risk_map": str(RISK_MAP_HTML)}, indent=2, ensure_ascii=False))
        return 0
    if args.mode == "demo-submit":
        result = process_realtime_inspection(_demo_payload(args.with_sample_gps), write_outputs=True)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if args.mode == "export-report":
        print(json.dumps(export_google_sheets_ready_csv(mode="dry-run"), indent=2, ensure_ascii=False))
        return 0
    if args.mode == "export-map":
        row = build_phase9_monitoring_row({**_demo_payload(args.with_sample_gps), "eta_days": 30.0, "eta_months": 0.99, "risk_priority": "CRITICAL"})
        print(json.dumps(write_phase9_risk_map(row), indent=2, ensure_ascii=False))
        return 0
    result = {
        "status": "PHASE12_ALL_DRY_RUN_READY",
        "pipeline": pipeline_status(),
        "demo_submit": process_realtime_inspection(_demo_payload(False), write_outputs=False),
        "report": export_google_sheets_ready_csv(mode="dry-run"),
        "map": {"status": "RISK_MAP_DRY_RUN_READY", "target": str(RISK_MAP_HTML), "writes_runtime": False},
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("PHASE12_ALL_DRY_RUN_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
