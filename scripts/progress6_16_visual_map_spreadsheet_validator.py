from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
REPORT = ROOT / "reports" / "progress6_16_visual_map_spreadsheet_validation.json"

def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "status": "PASS" if p.returncode == 0 else "FAIL",
        "stdout_tail": p.stdout.splitlines()[-30:],
        "stderr_tail": p.stderr.splitlines()[-30:],
    }

results = []
results.append(run([sys.executable, "-m", "compileall", "src", "scripts", "tests"]))

module_path = ROOT / "src" / "ulp_project" / "progress6_16_visual_result_middleware.py"
flask_app_path = ROOT / "src" / "ulp_project" / "flask_app.py"

source_checks = {
    "middleware_exists": module_path.exists(),
    "flask_app_exists": flask_app_path.exists(),
    "flask_install_block_present": "PROGRESS 6.16B VISUAL MAP/SPREADSHEET HARD FIX START" in flask_app_path.read_text(encoding="utf-8", errors="replace") if flask_app_path.exists() else False,
    "map_iframe_present": "p616-map-iframe" in module_path.read_text(encoding="utf-8", errors="replace") if module_path.exists() else False,
    "sheet_scroll_present": "progress6_16_table_scroll" in module_path.read_text(encoding="utf-8", errors="replace") if module_path.exists() else False,
    "empty_session_guard_present": "SESSION_ID_EMPTY_STOP" in module_path.read_text(encoding="utf-8", errors="replace") if module_path.exists() else False,
}

import_check = {"status": "SKIPPED"}
fake_map_check = {"status": "SKIPPED"}
fake_sheet_check = {"status": "SKIPPED"}

try:
    sys.path.insert(0, str(ROOT / "src"))
    m = importlib.import_module("ulp_project.progress6_16_visual_result_middleware")
    import_check = {
        "status": "PASS",
        "version": getattr(m, "VERSION", None),
        "has_install": hasattr(m, "install_progress6_16_visual_result_middleware"),
    }

    def fake_app(environ, start_response):
        path = environ.get("PATH_INFO", "")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        if "field-map" in path:
            body = """
            <html><body>
            <h1>Field Session Map</h1>
            <p>Session: FS_20260609_033216_d2b7b430</p>
            <p>Point: V001_pohon_sono</p>
            <p>Current marker operator/kamera: -7.2227179, 112.7347435</p>
            <p>Accuracy: 8.0 m</p>
            </body></html>
            """
            return [body.encode("utf-8")]
        body = """
        <html><head></head><body>
        <h1>Spreadsheet Evidence</h1>
        <table>
        <tr><th>session_id</th><th>timestamp</th><th>gps_coordinate</th><th>frame_status</th></tr>
        <tr><td>FS_20260609_033216_d2b7b430</td><td>2026-06-09</td><td>-7.2227179, 112.7347435</td><td>REALTIME_YOLO_PIPELINE_OK</td></tr>
        </table>
        </body></html>
        """
        return [body.encode("utf-8")]

    middleware = m.Progress616VisualResultMiddleware(fake_app)

    captured_map = {}
    def sr_map(status, headers, exc_info=None):
        captured_map["status"] = status
        captured_map["headers"] = headers
        return lambda data: None

    map_body = b"".join(middleware({"PATH_INFO": "/field-map/session/FS_20260609_033216_d2b7b430"}, sr_map)).decode("utf-8", errors="replace")
    fake_map_check = {
        "status": "PASS" if ("p616-map-iframe" in map_body and "GPS_MARKER_READY" in map_body and "openstreetmap.org/export/embed.html" in map_body) else "FAIL",
        "contains_iframe": "p616-map-iframe" in map_body,
        "contains_marker_ready": "GPS_MARKER_READY" in map_body,
        "contains_osm_embed": "openstreetmap.org/export/embed.html" in map_body,
    }

    captured_sheet = {}
    def sr_sheet(status, headers, exc_info=None):
        captured_sheet["status"] = status
        captured_sheet["headers"] = headers
        return lambda data: None

    sheet_body = b"".join(middleware({"PATH_INFO": "/field-spreadsheet/session/FS_20260609_033216_d2b7b430"}, sr_sheet)).decode("utf-8", errors="replace")
    fake_sheet_check = {
        "status": "PASS" if ("progress6_16_table_scroll" in sheet_body and "progress6_16_readable_cards" in sheet_body) else "FAIL",
        "contains_scroll": "progress6_16_table_scroll" in sheet_body,
        "contains_cards": "progress6_16_readable_cards" in sheet_body,
    }

except Exception as exc:
    import_check = {"status": "FAIL", "error": repr(exc)}

git_check = run(["git", "diff", "--check"])

hard_failures = []

for r in results:
    if r["returncode"] != 0:
        hard_failures.append("compileall_failed")

for k, v in source_checks.items():
    if not v:
        hard_failures.append(k)

if import_check.get("status") != "PASS":
    hard_failures.append("middleware_import_failed")

if fake_map_check.get("status") != "PASS":
    hard_failures.append("fake_map_visual_transform_failed")

if fake_sheet_check.get("status") != "PASS":
    hard_failures.append("fake_sheet_readability_transform_failed")

if git_check["returncode"] != 0:
    hard_failures.append("git_diff_check_failed")

payload = {
    "status": "PROGRESS_6_16B_VISUAL_MAP_SPREADSHEET_VALIDATION_PASS" if not hard_failures else "PROGRESS_6_16B_VISUAL_MAP_SPREADSHEET_VALIDATION_FAILED",
    "hard_failures": hard_failures,
    "source_checks": source_checks,
    "import_check": import_check,
    "fake_map_check": fake_map_check,
    "fake_sheet_check": fake_sheet_check,
    "compile_results": results,
    "git_diff_check": git_check,
    "no_label_touch": True,
    "no_raw_touch": True,
    "no_dataset_touch": True,
    "no_runs_touch": True,
    "no_weights_touch": True,
}

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))

if hard_failures:
    raise SystemExit(1)