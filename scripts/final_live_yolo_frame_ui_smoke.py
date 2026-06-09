from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\Projects\ULP_Project")
SRC = ROOT / "src"
REPORT = ROOT / "reports" / "final_live_yolo_frame_ui_smoke.json"

sys.path.insert(0, str(SRC))


def load_app():
    mod = importlib.import_module("ulp_project.flask_app")
    if hasattr(mod, "create_app"):
        return mod.create_app()
    if hasattr(mod, "app"):
        return mod.app
    if hasattr(mod, "get_app"):
        return mod.get_app()
    raise RuntimeError("APP_FACTORY_NOT_FOUND")


def main() -> int:
    result = {
        "version": "final_live_yolo_frame_ui_smoke",
        "status": "UNKNOWN",
        "hard_failures": [],
        "checks": {},
        "policy": {
            "frontend_core": "/api/field/session/frame",
            "blocked_legacy_core": "/api/field/session/vision-analyze",
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
        },
    }

    template = ROOT / "src" / "ulp_project" / "templates" / "field_camera.html"
    js = ROOT / "src" / "ulp_project" / "static" / "final_live_force_yolo_frame.js"
    css = ROOT / "src" / "ulp_project" / "static" / "final_live_compact_operator_ui.css"

    t = template.read_text(encoding="utf-8", errors="ignore")
    j = js.read_text(encoding="utf-8", errors="ignore") if js.exists() else ""
    c = css.read_text(encoding="utf-8", errors="ignore") if css.exists() else ""

    result["checks"]["files"] = {
        "template_exists": template.exists(),
        "js_exists": js.exists(),
        "css_exists": css.exists(),
    }

    result["checks"]["template"] = {
        "loads_final_live_js": "final_live_force_yolo_frame.js" in t,
        "loads_final_live_css": "final_live_compact_operator_ui.css" in t,
        "legacy_vision_js_removed": "progress6_22_vision_camera.js" not in t and "progress6_24_realtime_vision_switch.js" not in t,
    }

    result["checks"]["js"] = {
        "posts_frame_route": "/api/field/session/frame" in j,
        "redirects_vision_analyze": "/api/field/session/vision-analyze" in j and "legacy_vision_redirected_to_frame" in j,
        "has_1000ms_loop": "1000" in j and "setInterval" in j,
        "has_overlay_canvas": "final-live-yolo-overlay" in j,
        "has_compact_hud": "final-live-mini-hud" in j,
    }

    result["checks"]["css"] = {
        "has_compact_ui": "final-live-compact-ui" in c,
        "has_icon_chip": "final-live-icon-chip" in c,
    }

    app = load_app()
    client = app.test_client()
    resp = client.get("/field-camera?session_id=FS_FINAL_LIVE_SMOKE")
    html = resp.get_data(as_text=True)

    result["checks"]["flask_render"] = {
        "field_camera_status": resp.status_code,
        "html_loads_final_live_js": "final_live_force_yolo_frame.js" in html,
        "html_loads_final_live_css": "final_live_compact_operator_ui.css" in html,
        "html_not_loading_legacy_vision_switch": "progress6_24_realtime_vision_switch.js" not in html,
        "html_not_loading_legacy_vision_camera": "progress6_22_vision_camera.js" not in html,
    }

    for group in ("files", "template", "js", "css", "flask_render"):
        for k, v in result["checks"][group].items():
            if v is not True and not (k == "field_camera_status" and v == 200):
                result["hard_failures"].append(f"{group}.{k}={v}")

    if result["hard_failures"]:
        result["status"] = "FINAL_LIVE_YOLO_FRAME_UI_SMOKE_FAILED"
        code = 1
    else:
        result["status"] = "FINAL_LIVE_YOLO_FRAME_UI_SMOKE_PASS"
        code = 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
