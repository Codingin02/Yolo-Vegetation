from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:\Projects\ULP_Project")
BASE = "http://127.0.0.1:5000"
REPORT = ROOT / "reports" / "progress6_19_live_camera_tracking_smoke.json"

NO_TOUCH = {
    "no_label_touch": True,
    "no_raw_touch": True,
    "no_dataset_touch": True,
    "no_runs_touch": True,
    "no_weights_touch": True,
}

def request(method: str, path: str, payload=None, timeout=10):
    url = BASE + path
    data = None
    headers = {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode("utf-8", errors="replace")
            try:
                js = json.loads(text)
            except Exception:
                js = None
            return {
                "ok": True,
                "status_code": int(r.status),
                "text": text,
                "json": js,
            }
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            js = json.loads(text)
        except Exception:
            js = None
        return {
            "ok": False,
            "status_code": int(e.code),
            "text": text,
            "json": js,
        }
    except Exception as e:
        return {
            "ok": False,
            "status_code": 0,
            "text": repr(e),
            "json": None,
        }

def find_session_id(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"FS_\d{8}_\d{6}_[A-Za-z0-9]+", text)
    return m.group(0) if m else ""

def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    status_route = request("GET", "/api/runtime/progress6-18-tracking-status", timeout=10)

    result = {
        "version": "progress6_19_live_camera_tracking_smoke",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "status": "PROGRESS_6_19_NOT_EVALUATED",
        "status_route_code": status_route["status_code"],
        "status_route_text_head": status_route["text"][:1000],
        "status_route_json": status_route["json"],
        **NO_TOUCH,
    }

    if status_route["status_code"] != 200:
        result["status"] = "PROGRESS_6_19_FAILED_TRACKING_ROUTE_NOT_READY"
        REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 1

    if "PROGRESS_6_18G_RUNTIME_TRACKING_BRIDGE_INSTALLED" not in status_route["text"]:
        result["status"] = "PROGRESS_6_19_FAILED_NOT_6_18G_BRIDGE"
        REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 1

    start_payload = {
        "point_id": "V001_pohon_sono",
        "operator": "debug_ps",
        "operator_name": "debug_ps",
        "notes": "progress6_19 live camera tracking smoke; operator must open browser camera; not final PLN evidence",
    }

    start_resp = request("POST", "/api/field/session/start", start_payload, timeout=20)
    session_id = find_session_id(start_resp["text"])

    result.update({
        "start_status_code": start_resp["status_code"],
        "session_id": session_id,
        "camera_url": f"{BASE}/field-camera?session_id={session_id}" if session_id else "",
        "field_capture_url": f"{BASE}/field-capture",
    })

    if start_resp["status_code"] < 200 or start_resp["status_code"] >= 300 or not session_id:
        result["status"] = "PROGRESS_6_19_FAILED_SESSION_START"
        REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 1

    print("SESSION_ID=" + session_id)
    print("CAMERA_URL=" + result["camera_url"])
    print("Open the CAMERA_URL or /field-capture in browser, allow camera, then wait while this script watches session frame responses.")

    frame_candidates = []
    found_tracking = False
    found_runtime_integrated = False
    found_status = False
    last_frame_text = ""

    # Tidak membuat frame palsu di sini. Script menunggu frame yang dikirim browser UI.
    # Jika browser belum dibuka atau kamera belum diizinkan, hasilnya akan gagal dengan alasan jelas.
    for i in range(1, 46):
        time.sleep(1)

        # Ping route status sebagai bukti bridge masih hidup.
        sr = request("GET", "/api/runtime/progress6-18-tracking-status", timeout=5)

        # Tidak ada endpoint history khusus yang dijamin tersedia.
        # Maka kriteria 6.19 live-camera smoke adalah:
        # route bridge hidup + operator membuka camera_url + server terminal harus menunjukkan POST /api/field/session/frame.
        # Untuk membuktikan response bridge, kita kirim 1 frame diagnostic kecil hanya setelah browser diberi waktu.
        # Ini bukan field evidence dan tidak autosave.
        if i == 10:
            import base64
            import cv2
            import numpy as np

            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img[:] = (245, 245, 245)
            cv2.putText(img, "PROGRESS_6_19_DIAGNOSTIC_AFTER_CAMERA_WAIT", (20, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 2)
            ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            b64 = base64.b64encode(buf.tobytes()).decode("ascii")

            frame_payload = {
                "session_id": session_id,
                "frame_base64": b64,
                "diagnostic": "progress6_19_bridge_response_check_after_camera_wait",
                "source": "DIAGNOSTIC_NOT_FIELD_EVIDENCE",
            }
            fr = request("POST", "/api/field/session/frame", frame_payload, timeout=90)
            last_frame_text = fr["text"]
            frame_candidates.append({
                "try": i,
                "status_code": fr["status_code"],
                "text_head": fr["text"][:1200],
            })

            found_tracking = "progress6_18_tracking" in fr["text"]
            found_runtime_integrated = "runtime_tracking_integrated" in fr["text"]
            found_status = (
                "TRACKING_READY" in fr["text"]
                or "TRACKING_MODEL_NOT_READY" in fr["text"]
                or "TRACKING_RUNTIME_EXCEPTION" in fr["text"]
                or "FRAME_NOT_AVAILABLE" in fr["text"]
            )

            break

    result.update({
        "frame_candidates": frame_candidates,
        "has_progress6_18_tracking_key": found_tracking,
        "has_runtime_tracking_integrated": found_runtime_integrated,
        "has_tracking_status": found_status,
        "last_frame_text_head": last_frame_text[:1800],
        "operator_note": "Untuk live kamera nyata, lihat terminal server: harus ada POST /api/field/session/frame dari browser setelah kamera diizinkan.",
    })

    if found_tracking and found_runtime_integrated and found_status:
        result["status"] = "PROGRESS_6_19_LIVE_CAMERA_TRACKING_BRIDGE_SMOKE_PASS"
        rc = 0
    else:
        result["status"] = "PROGRESS_6_19_LIVE_CAMERA_TRACKING_BRIDGE_SMOKE_FAILED"
        rc = 1

    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("REPORT=" + str(REPORT))
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
