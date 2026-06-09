import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.flask_app import create_app

files = {
    "camera_template": ROOT / "src/ulp_project/templates/field_camera.html",
    "js": ROOT / "src/ulp_project/static/progress6_24_realtime_vision_switch.js",
    "css25": ROOT / "src/ulp_project/static/progress6_25_abort_fix.css",
}

texts = {k: p.read_text(encoding="utf-8", errors="replace") for k, p in files.items()}

app = create_app()
routes = sorted(str(rule.rule) for rule in app.url_map.iter_rules())

checks = {
    "field_camera_route_exists": "/field-camera" in routes,
    "vision_analyze_route_exists": "/api/field/session/vision-analyze" in routes,
    "shutter_route_exists": "/api/field/session/shutter" in routes,
    "template_has_625_css": "progress6_25_abort_fix.css" in texts["camera_template"],
    "js_timeout_18s": "const REQUEST_TIMEOUT_MS = 18000;" in texts["js"],
    "js_cloud_min_interval_5s": "const CLOUD_MIN_INTERVAL_MS = 5000;" in texts["js"],
    "js_uses_cloud_min_interval": "elapsed < CLOUD_MIN_INTERVAL_MS - 50" in texts["js"],
    "js_abort_has_reason": "P625_VISION_CLOUD_TIMEOUT_AFTER_18S" in texts["js"],
    "js_normalizes_abort_error": "VISION_TIMEOUT_CLIENT_ABORT_PREVENTED_BY_P625_RELOAD_REQUIRED" in texts["js"],
    "js_caches_last_result": "P625_LAST_VISION_RESULT" in texts["js"],
    "js_attaches_cache_to_shutter": "vision_result_cache_status" in texts["js"],
    "js_exposes_patch_status": 'patch_6_25: "ABORT_FIX_CLOUD_SAFE"' in texts["js"],
    "css_hides_legacy_summary": "#p622VisionSummary" in texts["css25"],
    "css_compacts_prediction_panel": "max-height: 78px" in texts["css25"],
    "no_api_key_in_js": "GEMINI_API_KEY" not in texts["js"] and "OPENROUTER_API_KEY" not in texts["js"] and "GROQ_API_KEY" not in texts["js"],
}

report = {
    "version": "progress6_25_abort_fix_smoke",
    "status": "PROGRESS_6_25_ABORT_FIX_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_25_ABORT_FIX_SMOKE_FAILED",
    "checks": checks,
    "route_count": len(routes),
    "note": "Fixes aggressive frontend abort and keeps cloud vision latest-only.",
}

out = ROOT / "reports" / "progress6_25_abort_fix_smoke.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(report, indent=2, ensure_ascii=False))

if report["status"] != "PROGRESS_6_25_ABORT_FIX_SMOKE_PASS":
    raise SystemExit(report["status"])

print("PROGRESS_6_25_ABORT_FIX_SMOKE_PASS")
