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
    "capture_template": ROOT / "src/ulp_project/templates/field_capture.html",
    "vision_js": ROOT / "src/ulp_project/static/progress6_22_vision_camera.js",
    "capture_js": ROOT / "src/ulp_project/static/progress6_22_capture_start_guard.js",
    "vision_css": ROOT / "src/ulp_project/static/progress6_22_vision_camera.css",
}

texts = {k: p.read_text(encoding="utf-8", errors="replace") for k, p in files.items()}

app = create_app()
routes = sorted(str(rule.rule) for rule in app.url_map.iter_rules())

checks = {
    "route_vision_status": "/api/runtime/progress6-22-vision-status" in routes,
    "route_vision_analyze": "/api/field/session/vision-analyze" in routes,
    "camera_template_has_vision_js": "progress6_22_vision_camera.js" in texts["camera_template"],
    "camera_template_has_css": "progress6_22_vision_camera.css" in texts["camera_template"],
    "capture_template_has_start_guard": "progress6_22_capture_start_guard.js" in texts["capture_template"],
    "vision_js_has_endpoint": "/api/field/session/vision-analyze" in texts["vision_js"],
    "vision_js_has_1000_box_contract": "normalized 0-1000" in texts["vision_js"] or "0-1000" in texts["vision_js"],
    "vision_js_hides_legacy_yolo_canvas": "p622-hidden-legacy-canvas" in texts["vision_js"],
    "vision_js_shutter_hook": "installShutterHook" in texts["vision_js"],
    "vision_js_no_key_in_frontend": "GEMINI_API_KEY" not in texts["vision_js"] and "OPENROUTER_API_KEY" not in texts["vision_js"] and "GROQ_API_KEY" not in texts["vision_js"],
    "capture_guard_non_json_error": "SESSION_START_RETURNED_NON_JSON" in texts["capture_js"],
    "css_clean_mode": "p622-clean-vision-mode" in texts["vision_css"],
}

report = {
    "version": "progress6_22_frontend_vision_overlay_smoke",
    "status": "PROGRESS_6_22_FRONTEND_VISION_OVERLAY_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_22_FRONTEND_VISION_OVERLAY_SMOKE_FAILED",
    "checks": checks,
    "route_count": len(routes),
}

out = ROOT / "reports" / "progress6_22_frontend_vision_overlay_smoke.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(report, indent=2, ensure_ascii=False))

if report["status"] != "PROGRESS_6_22_FRONTEND_VISION_OVERLAY_SMOKE_PASS":
    raise SystemExit(report["status"])

print("PROGRESS_6_22_FRONTEND_VISION_OVERLAY_SMOKE_PASS")
