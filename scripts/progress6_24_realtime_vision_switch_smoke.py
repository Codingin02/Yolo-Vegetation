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
    "css": ROOT / "src/ulp_project/static/progress6_24_realtime_vision_switch.css",
    "js": ROOT / "src/ulp_project/static/progress6_24_realtime_vision_switch.js",
}

texts = {k: p.read_text(encoding="utf-8", errors="replace") for k, p in files.items()}

app = create_app()
routes = sorted(str(rule.rule) for rule in app.url_map.iter_rules())

checks = {
    "field_camera_route_exists": "/field-camera" in routes,
    "vision_analyze_route_exists": "/api/field/session/vision-analyze" in routes,
    "session_frame_route_exists": "/api/field/session/frame" in routes,
    "session_shutter_route_exists": "/api/field/session/shutter" in routes,
    "camera_template_has_6_24_css": "progress6_24_realtime_vision_switch.css" in texts["camera_template"],
    "camera_template_has_6_24_js": "progress6_24_realtime_vision_switch.js" in texts["camera_template"],
    "js_has_vision_endpoint": "/api/field/session/vision-analyze" in texts["js"],
    "js_has_interval_1000": "LOOP_INTERVAL_MS = 1000" in texts["js"],
    "js_has_switch": "p624SwitchWrap" in texts["js"] and "setRunning" in texts["js"],
    "js_suppresses_legacy_frame": "P624_LEGACY_FRAME_SUPPRESSED" in texts["js"],
    "js_suppresses_shutter_vision": "P624_SHUTTER_VISION_SUPPRESSED" in texts["js"],
    "js_has_latest_only_pending_guard": "if (state.pending) return" in texts["js"],
    "js_has_abort_controller": "AbortController" in texts["js"],
    "js_has_colored_groups": "struktur_penyangga" in texts["js"] and "konduktor" in texts["js"] and "pohon_sono_candidate" in texts["js"] and "general_object" in texts["js"],
    "css_has_icon_hud": "p624IconHud" in texts["css"],
    "css_has_switch": "p624SwitchWrap" in texts["css"],
    "css_has_colored_legend": "p624-blue" in texts["css"] and "p624-yellow" in texts["css"] and "p624-green" in texts["css"] and "p624-gray" in texts["css"],
    "js_no_api_key": "GEMINI_API_KEY" not in texts["js"] and "OPENROUTER_API_KEY" not in texts["js"] and "GROQ_API_KEY" not in texts["js"],
}

report = {
    "version": "progress6_24_realtime_vision_switch_smoke",
    "status": "PROGRESS_6_24_REALTIME_VISION_SWITCH_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_24_REALTIME_VISION_SWITCH_SMOKE_FAILED",
    "checks": checks,
    "route_count": len(routes),
    "note": "Switch-controlled realtime Vision API. Shutter remains documentation only.",
}

out = ROOT / "reports" / "progress6_24_realtime_vision_switch_smoke.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(report, indent=2, ensure_ascii=False))

if report["status"] != "PROGRESS_6_24_REALTIME_VISION_SWITCH_SMOKE_PASS":
    raise SystemExit(report["status"])

print("PROGRESS_6_24_REALTIME_VISION_SWITCH_SMOKE_PASS")
