import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:5000"

def find_image():
    for pattern in [
        "data/raw/00_inbox_hp/images/V001*.jpg",
        "data/raw/00_inbox_hp/images/V002*.jpg",
        "data/raw/00_inbox_hp/images/*.jpg",
    ]:
        found = list(ROOT.glob(pattern))
        found = [p for p in found if p.is_file()]
        if found:
            return found[0]
    raise SystemExit("NO_TEST_IMAGE_FOUND")

def http_json(method, url, payload=None, timeout=80):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return int(resp.status), json.loads(raw)

def main():
    image = find_image()
    img_b64 = base64.b64encode(image.read_bytes()).decode("utf-8")

    report = {
        "version": "progress6_22_vision_runtime_backend_smoke",
        "image": str(image.relative_to(ROOT)),
        "gemini_key_present": bool(os.environ.get("GEMINI_API_KEY")),
        "openrouter_key_present": bool(os.environ.get("OPENROUTER_API_KEY")),
    }

    try:
        status_code, status_json = http_json("GET", BASE + "/api/runtime/progress6-22-vision-status", None, timeout=10)
        report["status_route_code"] = status_code
        report["status_route_json"] = status_json
    except Exception as e:
        report["status"] = "PROGRESS_6_22_VISION_BACKEND_SMOKE_FAILED"
        report["error"] = "STATUS_ROUTE_FAILED: " + repr(e)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        raise SystemExit(report["status"])

    payload = {
        "session_id": "SMOKE_PROGRESS_6_22",
        "image_base64": img_b64,
        "source": "SMOKE_TEST_LOCAL_IMAGE_NOT_FIELD_LIVE",
    }

    try:
        analyze_code, analyze_json = http_json("POST", BASE + "/api/field/session/vision-analyze", payload, timeout=100)
        report["analyze_status_code"] = analyze_code
        report["analyze_json"] = analyze_json
    except Exception as e:
        report["status"] = "PROGRESS_6_22_VISION_BACKEND_SMOKE_FAILED"
        report["error"] = "VISION_ANALYZE_FAILED: " + repr(e)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        raise SystemExit(report["status"])

    detections = report["analyze_json"].get("detections", [])
    boxes = report["analyze_json"].get("overlay_json", {}).get("boxes", [])

    report["checks"] = {
        "status_route_ok": report.get("status_route_code") == 200,
        "analyze_route_ok": report.get("analyze_status_code") == 200,
        "detections_is_list": isinstance(detections, list),
        "overlay_boxes_is_list": isinstance(boxes, list),
        "no_fake_detection": report["analyze_json"].get("no_fake_detection") is True,
        "no_fake_clearance": report["analyze_json"].get("no_fake_clearance") is True,
    }

    report["status"] = "PROGRESS_6_22_VISION_BACKEND_SMOKE_PASS" if all(report["checks"].values()) else "PROGRESS_6_22_VISION_BACKEND_SMOKE_FAILED"

    out = ROOT / "reports" / "progress6_22_vision_runtime_backend_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if report["status"] != "PROGRESS_6_22_VISION_BACKEND_SMOKE_PASS":
        raise SystemExit(report["status"])

    print("PROGRESS_6_22_VISION_BACKEND_SMOKE_PASS")

if __name__ == "__main__":
    main()
