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
    "css": ROOT / "src/ulp_project/static/progress6_23_ios_glass_3d_ui.css",
    "js": ROOT / "src/ulp_project/static/progress6_23_ios_glass_3d_ui.js",
}

texts = {k: p.read_text(encoding="utf-8", errors="replace") for k, p in files.items()}

app = create_app()
routes = sorted(str(rule.rule) for rule in app.url_map.iter_rules())

checks = {
    "field_camera_route_exists": "/field-camera" in routes,
    "field_capture_route_exists": "/field-capture" in routes,
    "vision_analyze_route_still_exists": "/api/field/session/vision-analyze" in routes,
    "camera_template_has_6_23_css": "progress6_23_ios_glass_3d_ui.css" in texts["camera_template"],
    "camera_template_has_6_23_js": "progress6_23_ios_glass_3d_ui.js" in texts["camera_template"],
    "capture_template_has_6_23_css": "progress6_23_ios_glass_3d_ui.css" in texts["capture_template"],
    "capture_template_has_6_23_js": "progress6_23_ios_glass_3d_ui.js" in texts["capture_template"],
    "css_has_3d_transform": "translateZ" in texts["css"] and "perspective" in texts["css"],
    "css_has_glass_backdrop": "backdrop-filter" in texts["css"] and "-webkit-backdrop-filter" in texts["css"],
    "css_has_leaf_fiber": "leaf-fiber" in texts["css"] or "repeating-linear-gradient" in texts["css"],
    "css_has_ripple": "p623-ripple" in texts["css"],
    "css_has_shutter_3d": "p623-shutter-3d" in texts["css"],
    "js_has_haptic": "navigator.vibrate" in texts["js"],
    "js_has_element_animate": ".animate(" in texts["js"],
    "js_has_mutation_observer": "MutationObserver" in texts["js"],
    "js_no_api_key": "GEMINI_API_KEY" not in texts["js"] and "OPENROUTER_API_KEY" not in texts["js"] and "GROQ_API_KEY" not in texts["js"],
    "js_detection_backend_unchanged": "/api/field/session/vision-analyze" not in texts["js"],
}

report = {
    "version": "progress6_23_ios_glass_3d_ui_smoke",
    "status": "PROGRESS_6_23_IOS_GLASS_3D_UI_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_23_IOS_GLASS_3D_UI_SMOKE_FAILED",
    "checks": checks,
    "route_count": len(routes),
    "note": "UI-only smoke. Vision backend remains from Progress 6.22.",
}

out = ROOT / "reports" / "progress6_23_ios_glass_3d_ui_smoke.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(report, indent=2, ensure_ascii=False))

if report["status"] != "PROGRESS_6_23_IOS_GLASS_3D_UI_SMOKE_PASS":
    raise SystemExit(report["status"])

print("PROGRESS_6_23_IOS_GLASS_3D_UI_SMOKE_PASS")
