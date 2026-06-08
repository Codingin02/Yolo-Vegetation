from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def run_smoke() -> dict[str, object]:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        client = create_app(runtime_root=Path(tmp)).test_client()
        start = client.post(
            "/api/field/session/start",
            json={"gps": {"latitude": -7.2234567, "longitude": 112.7312345, "accuracy": 5.0}, "camera_status": "CAMERA_READY"},
        ).get_json()
        session_id = start["session_id"]
        locked_map = client.get(f"/field-map/session/{session_id}")
        shutter = client.post("/api/field/session/shutter", json={"session_id": session_id, "idempotency_key": "P69_MAP_SHEET"})
        shutter_payload = shutter.get_json() or {}
        map_page = client.get(shutter_payload.get("map_url") or f"/field-map/session/{session_id}")
        sheet_page = client.get(shutter_payload.get("spreadsheet_url") or f"/field-spreadsheet/session/{session_id}")
        locked_html = locked_map.get_data(as_text=True)
        map_html = map_page.get_data(as_text=True)
        sheet_html = sheet_page.get_data(as_text=True)
    checks = {
        "map_locked_before_shutter": locked_map.status_code == 200 and "MAP_LOCKED_SHUTTER_REQUIRED" in locked_html,
        "shutter_saved": shutter.status_code not in {404, 405, 500} and shutter_payload.get("status") == "FIELD_SESSION_SHUTTER_SAVED",
        "map_enabled_after_shutter": shutter_payload.get("map_enabled") is True,
        "result_enabled_after_shutter": shutter_payload.get("result_enabled") is True,
        "map_html_after_shutter": map_page.status_code == 200 and "<html" in map_html.lower() and '"status"' not in map_html[:80],
        "spreadsheet_html_after_shutter": sheet_page.status_code == 200 and "Spreadsheet Evidence" in sheet_html,
        "local_csv_ready": "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_SPREADSHEET_READY" in sheet_html and "Download CSV" in sheet_html,
        "growth_in_spreadsheet": "growth_selected_model" in sheet_html,
    }
    return {
        "status": "PROGRESS_6_9_MAP_SPREADSHEET_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_9_MAP_SPREADSHEET_SMOKE_FAIL",
        "checks": checks,
        "session_id": session_id,
        "map_url": shutter_payload.get("map_url"),
        "spreadsheet_url": shutter_payload.get("spreadsheet_url"),
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
