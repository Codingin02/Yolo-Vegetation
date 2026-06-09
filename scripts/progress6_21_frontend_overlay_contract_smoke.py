from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_smoke() -> dict[str, object]:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_camera.js").read_text(encoding="utf-8")
    gps_js = (ROOT / "src" / "ulp_project" / "static" / "progress6_20_gps_reliability.js").read_text(encoding="utf-8")
    html = (ROOT / "src" / "ulp_project" / "templates" / "field_camera.html").read_text(encoding="utf-8")

    js_index_overlay = js.find("result?.overlay_json?.boxes")
    js_index_top = js.find("result?.detections")
    js_index_p620 = js.find("result?.progress6_20_gps_yolo?.yolo_detection?.detections")

    checks = {
        "reads_progress6_20_gps_yolo": "progress6_20_gps_yolo" in js,
        "overlay_priority_first": -1 not in {js_index_overlay, js_index_top, js_index_p620} and js_index_overlay < js_index_top < js_index_p620,
        "draw_overlay_function_exists": "function drawOverlay" in js and "strokeRect" in js,
        "bbox_xyxy_supported": "bbox_xyxy" in js,
        "video_native_frame_source": "ctxFrame.drawImage(video" in js,
        "canvas_matches_video_size": "canvas.width = Math.max(1, Math.round(video.videoWidth))" in js
        and "canvas.height = Math.max(1, Math.round(video.videoHeight))" in js,
        "jpeg_quality_085": 'toDataURL("image/jpeg", 0.85)' in js,
        "camera_front_warning": "CAMERA_FRONT_ACTIVE_NOT_RECOMMENDED_FOR_FIELD_TREE" in js,
        "cache_busting_progress6_21": "field_camera.js?v=progress6_21_live_yolo_overlay" in html
        and "field_camera.css?v=progress6_21_live_yolo_overlay" in html,
        "progress6_11_not_main_version": "field_camera.js?v=progress6_11" not in html
        and "field_camera.css?v=progress6_11" not in html,
        "ui_version_progress6_21": "PROGRESS_6_21_LIVE_YOLO_OVERLAY" in js and "PROGRESS_6_21_LIVE_YOLO_OVERLAY" in html,
        "yolo_not_blocked_not_primary_badge": "YOLO_NOT_BLOCKED" not in gps_js and "YOLO_NOT_BLOCKED" not in html,
        "developer_debug_collapsed": "<details" in html and "Developer Debug" in html,
    }

    return {
        "status": "PROGRESS_6_21_FRONTEND_OVERLAY_CONTRACT_PASS" if all(checks.values()) else "PROGRESS_6_21_FRONTEND_OVERLAY_CONTRACT_FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
