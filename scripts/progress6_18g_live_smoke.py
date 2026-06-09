from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path.cwd()
REPORT = ROOT / "reports" / "progress6_18g_runtime_tracking_live_smoke.json"
BASE = "http://127.0.0.1:5000"


def request_json(method: str, url: str, payload=None, timeout=30):
    data = None
    headers = {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                js = json.loads(text)
            except Exception:
                js = None
            return resp.status, text, js
    except HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        return e.code, text, None
    except URLError as e:
        return 0, str(e), None


def find_session_id(text: str) -> str:
    m = re.search(r"FS_\d{8}_\d{6}_[A-Za-z0-9]+", text or "")
    return m.group(0) if m else ""


def make_synthetic_frame_b64() -> str:
    try:
        import cv2
        import numpy as np
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (245, 245, 245)
        cv2.rectangle(img, (260, 80), (390, 420), (60, 140, 60), -1)
        cv2.circle(img, (325, 90), 70, (40, 160, 40), -1)
        cv2.putText(img, "PROGRESS_6_18G_SYNTHETIC_NOT_FIELD", (25, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 2)
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if ok:
            return base64.b64encode(buf.tobytes()).decode("ascii")
    except Exception:
        pass

    return base64.b64encode(b"PROGRESS_6_18G_SYNTHETIC_NOT_FIELD").decode("ascii")


def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    status_code, status_text, status_json = request_json("GET", f"{BASE}/api/runtime/progress6-18-tracking-status", timeout=10)

    start_code, start_text, start_json = request_json("POST", f"{BASE}/api/field/session/start", {
        "point_id": "V001_pohon_sono",
        "operator": "debug_ps",
        "operator_name": "debug_ps",
        "notes": "progress6_18g live smoke; synthetic frame, not field evidence",
    }, timeout=30)

    session_id = find_session_id(start_text)

    frame_code = 0
    frame_text = ""
    frame_json = None

    if session_id:
        frame_code, frame_text, frame_json = request_json("POST", f"{BASE}/api/field/session/frame", {
            "session_id": session_id,
            "frame_base64": make_synthetic_frame_b64(),
            "diagnostic": "progress6_18g_runtime_tracking_synthetic_not_field_data",
            "source": "SYNTHETIC_DIAGNOSTIC_NOT_FIELD_EVIDENCE",
        }, timeout=120)

    has_tracking_key = "progress6_18_tracking" in (frame_text or "")
    has_runtime_integrated = "runtime_tracking_integrated" in (frame_text or "")
    has_tracking_status = any(x in (frame_text or "") for x in [
        "TRACKING_READY",
        "TRACKING_MODEL_NOT_READY",
        "TRACKING_RUNTIME_EXCEPTION",
        "FRAME_NOT_AVAILABLE",
    ])

    result = {
        "version": "progress6_18g_live_smoke",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "PROGRESS_6_18G_RUNTIME_TRACKING_LIVE_SMOKE_PASS"
        if status_code == 200 and 200 <= start_code < 300 and 200 <= frame_code < 300 and has_tracking_key and has_runtime_integrated and has_tracking_status
        else "PROGRESS_6_18G_RUNTIME_TRACKING_LIVE_SMOKE_FAILED",
        "status_route_code": status_code,
        "status_route_json": status_json,
        "status_route_text_head": (status_text or "")[:1000],
        "start_status_code": start_code,
        "session_id": session_id,
        "frame_status_code": frame_code,
        "has_progress6_18_tracking_key": has_tracking_key,
        "has_runtime_tracking_integrated": has_runtime_integrated,
        "has_tracking_status": has_tracking_status,
        "frame_json_keys": sorted(frame_json.keys()) if isinstance(frame_json, dict) else [],
        "frame_text_head": (frame_text or "")[:2000],
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_dataset_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
    }

    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
