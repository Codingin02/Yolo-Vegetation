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


def text_has_realtime_loop(*texts: str) -> bool:
    merged = "\n".join(t or "" for t in texts)

    if "setInterval" in merged and ("1000" in merged or "FRAME_INTERVAL" in merged or "intervalMs" in merged or "loopMs" in merged):
        return True

    if "requestAnimationFrame" in merged and "/api/field/session/frame" in merged:
        return True

    if "setTimeout" in merged and ("1000" in merged or "FRAME_INTERVAL" in merged or "intervalMs" in merged or "loopMs" in merged):
        return True

    if "YOLO_FIRST" in merged and "/api/field/session/frame" in merged and ("clearInterval" in merged or "AbortController" in merged):
        return True

    return False


def main() -> int:
    result = {
        "version": "final_live_yolo_frame_ui_smoke_v2_progress7",
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
    js_final = ROOT / "src" / "ulp_project" / "static" / "final_live_force_yolo_frame.js"
    js_camera = ROOT / "src" / "ulp_project" / "static" / "field_camera.js"
    js_lock = ROOT / "src" / "ulp_project" / "static" / "progress6_27_yolo_first_lock.js"
    css = ROOT / "src" / "ulp_project" / "static" / "final_live_compact_operator_ui.css"

    t = template.read_text(encoding="utf-8", errors="ignore") if template.exists() else ""
    j_final = js_final.read_text(encoding="utf-8", errors="ignore") if js_final.exists() else ""
    j_camera = js_camera.read_text(encoding="utf-8", errors="ignore") if js_camera.exists() else ""
    j_lock = js_lock.read_text(encoding="utf-8", errors="ignore") if js_lock.exists() else ""
    c = css.read_text(encoding="utf-8", errors="ignore") if css.exists() else ""

    all_js = "\n".join([j_final, j_camera, j_lock])

    result["checks"]["files"] = {
        "template_exists": template.exists(),
        "js_final_exists": js_final.exists(),
        "js_camera_exists": js_camera.exists(),
        "css_exists": css.exists(),
    }

    result["checks"]["template"] = {
        "loads_final_live_js": "final_live_force_yolo_frame.js" in t,
        "loads_final_live_css": "final_live_compact_operator_ui.css" in t,
        "legacy_vision_js_removed": "progress6_22_vision_camera.js" not in t and "progress6_24_realtime_vision_switch.js" not in t,
    }

    result["checks"]["js"] = {
        "posts_frame_route": "/api/field/session/frame" in all_js,
        "redirects_vision_analyze": "/api/field/session/vision-analyze" in all_js and ("legacy_vision_redirected_to_frame" in all_js or "/api/field/session/frame" in all_js),
        "has_realtime_loop": text_has_realtime_loop(j_final, j_camera, j_lock),
        "has_overlay_canvas": "final-live-yolo-overlay" in all_js or "overlay" in all_js.lower(),
        "has_compact_hud": "final-live-mini-hud" in all_js or "compact" in all_js.lower(),
        "has_off_stop_mechanism": "clearInterval" in all_js or "AbortController" in all_js or "YOLO-FIRST OFF" in all_js or "yoloOff" in all_js,
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
        "html_no_model_status_unknown": "MODEL_STATUS_UNKNOWN" not in html,
    }

    for group, checks in result["checks"].items():
        for k, v in checks.items():
            if k == "field_camera_status":
                if v != 200:
                    result["hard_failures"].append(f"{group}.{k}={v}")
            elif v is not True:
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
