from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:5000"
REPORT = ROOT / "reports" / "progress6_20_gps_yolo_live_smoke.json"
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"

MODEL_CANDIDATES = [
    ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt",
    ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt",
]

IMAGE_ROOTS = [
    ROOT / "data" / "raw" / "01_field_points",
    ROOT / "data" / "raw" / "00_inbox_hp" / "images",
    ROOT / "data" / "raw" / "00_inbox_hp",
]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_report(obj: Dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def request_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Tuple[int, str, Optional[Dict[str, Any]]]:
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
                return resp.status, text, json.loads(text)
            except Exception:
                return resp.status, text, None
    except HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, text, json.loads(text)
        except Exception:
            return exc.code, text, None
    except URLError as exc:
        return 0, repr(exc), None


def find_session_id(text: str) -> str:
    m = re.search(r"FS_\d{8}_\d{6}_[A-Za-z0-9]+", text or "")
    return m.group(0) if m else ""


def find_model() -> Optional[Path]:
    for p in MODEL_CANDIDATES:
        if p.exists():
            return p
    return None


def candidate_images() -> List[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    out: List[Path] = []

    for root in IMAGE_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.suffix.lower() not in exts:
                continue
            low = str(p).lower()
            if "dataset_botol" in low:
                continue
            if ("v001" in low or "v002" in low or "v003" in low or "v004" in low or "v005" in low or "pohon_sono" in low or "sono" in low):
                out.append(p)

    def score(p: Path) -> tuple:
        low = str(p).lower()
        return (
            0 if "pohon_sono" in low else 1,
            0 if "v001" in low else 1,
            len(str(p)),
        )

    out = sorted(list(dict.fromkeys(out)), key=score)
    return out[:80]


def run_direct_yolo_scan(images: List[Path]) -> Dict[str, Any]:
    model_path = find_model()
    if model_path is None:
        return {
            "status": "DIRECT_YOLO_MODEL_NOT_FOUND",
            "model_path": None,
            "selected_image": None,
            "tree_detected": False,
            "detection_count": 0,
            "detections": [],
        }

    try:
        from ultralytics import YOLO
        model = YOLO(str(model_path))
    except Exception as exc:
        return {
            "status": "DIRECT_YOLO_IMPORT_OR_LOAD_FAILED",
            "model_path": str(model_path.relative_to(ROOT)),
            "exception": repr(exc),
            "selected_image": None,
            "tree_detected": False,
            "detection_count": 0,
            "detections": [],
        }

    checked = []
    for img_path in images:
        try:
            results = model.predict(source=str(img_path), conf=0.25, verbose=False)
            detections = []
            names = getattr(model, "names", {}) or {}

            for r in results or []:
                boxes = getattr(r, "boxes", None)
                if boxes is None:
                    continue

                xyxy = boxes.xyxy.cpu().numpy().tolist() if boxes.xyxy is not None else []
                cls_list = boxes.cls.cpu().numpy().tolist() if boxes.cls is not None else []
                conf_list = boxes.conf.cpu().numpy().tolist() if boxes.conf is not None else []

                for i, box in enumerate(xyxy):
                    cls_id = int(cls_list[i]) if i < len(cls_list) else 0
                    conf = float(conf_list[i]) if i < len(conf_list) else 0.0
                    cls_name = str(names.get(cls_id, cls_id))
                    if cls_id == 0 or cls_name.lower() in {"pohon_sono", "tree_sono", "sono"}:
                        detections.append({
                            "class_id": cls_id,
                            "class_name": cls_name,
                            "confidence": round(conf, 4),
                            "bbox_xyxy": [round(float(v), 2) for v in box],
                        })

            checked.append({
                "image": str(img_path.relative_to(ROOT)),
                "detection_count": len(detections),
            })

            if detections:
                return {
                    "status": "DIRECT_YOLO_POHON_SONO_DETECTED",
                    "model_path": str(model_path.relative_to(ROOT)),
                    "selected_image": str(img_path.relative_to(ROOT)),
                    "tree_detected": True,
                    "detection_count": len(detections),
                    "detections": detections,
                    "checked_preview": checked[:20],
                }
        except Exception as exc:
            checked.append({
                "image": str(img_path.relative_to(ROOT)),
                "error": repr(exc),
            })

    return {
        "status": "DIRECT_YOLO_READY_BUT_NO_TREE_DETECTED_IN_CANDIDATE_IMAGES",
        "model_path": str(model_path.relative_to(ROOT)),
        "selected_image": None,
        "tree_detected": False,
        "detection_count": 0,
        "detections": [],
        "checked_preview": checked[:40],
        "note": "Tidak ada fake detection. Tambahkan/arah kamera ke pohon_sono yang jelas bila ini gagal.",
    }


def image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> int:
    result: Dict[str, Any] = {
        "version": "progress6_20_gps_yolo_live_smoke",
        "timestamp": now(),
        "status": "PROGRESS_6_20_GPS_YOLO_LIVE_SMOKE_FAILED",
        "hard_failures": [],
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_dataset_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
    }

    status_code, status_text, status_json = request_json("GET", f"{BASE}/api/runtime/progress6-20-gps-yolo-status", timeout=10)
    result["status_route_code"] = status_code
    result["status_route_json"] = status_json
    result["status_route_text_head"] = status_text[:1000]

    if status_code != 200:
        result["hard_failures"].append("status_route_not_200")
        write_report(result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1

    images = candidate_images()
    result["candidate_image_count"] = len(images)
    result["candidate_images_preview"] = [str(p.relative_to(ROOT)) for p in images[:20]]

    direct = run_direct_yolo_scan(images)
    result["direct_yolo_scan"] = direct

    if not direct.get("tree_detected"):
        result["hard_failures"].append("direct_yolo_tree_detection_not_confirmed")
        write_report(result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1

    selected_rel = direct.get("selected_image")
    selected_abs = ROOT / selected_rel

    start_payload = {
        "point_id": "V001_pohon_sono",
        "operator": "debug_ps",
        "operator_name": "debug_ps",
        "notes": "progress6_20 GPS reliability + YOLO pohon_sono detection smoke; selected local V/pohon_sono image, not new field capture",
    }

    start_code, start_text, start_json = request_json("POST", f"{BASE}/api/field/session/start", start_payload, timeout=30)
    session_id = find_session_id(start_text)

    result["start_status_code"] = start_code
    result["session_id"] = session_id

    if start_code < 200 or start_code >= 300 or not session_id:
        result["hard_failures"].append("session_start_failed")
        write_report(result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1

    gps_payload = {
        "session_id": session_id,
        "latitude": -7.2227179,
        "longitude": 112.7347435,
        "accuracy": 8.0,
        "gps_accuracy_m": 8.0,
        "gps_status": "GPS_READY_MANUAL_DIAGNOSTIC_PROGRESS_6_20",
        "gps_source": "MANUAL_DIAGNOSTIC_NOT_FIELD_GPS",
        "source": "MANUAL_DIAGNOSTIC_NOT_FIELD_GPS",
        "gps": {
            "latitude": -7.2227179,
            "longitude": 112.7347435,
            "accuracy": 8.0,
        },
        "coords": {
            "latitude": -7.2227179,
            "longitude": 112.7347435,
            "accuracy": 8.0,
        },
    }

    gps_code, gps_text, gps_json = request_json("POST", f"{BASE}/api/field/session/gps-update", gps_payload, timeout=30)
    result["gps_update_status_code"] = gps_code
    result["gps_update_json"] = gps_json

    if gps_code < 200 or gps_code >= 300:
        result["hard_failures"].append("gps_update_failed")
        write_report(result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1

    frame_payload = {
        "session_id": session_id,
        "frame_base64": image_to_base64(selected_abs),
        "source": "LOCAL_POHON_SONO_IMAGE_SMOKE_NOT_NEW_FIELD_CAPTURE",
        "diagnostic": "progress6_20_gps_yolo_detection_smoke",
    }

    frame_code, frame_text, frame_json = request_json("POST", f"{BASE}/api/field/session/frame", frame_payload, timeout=180)
    result["frame_status_code"] = frame_code
    result["frame_json_keys"] = sorted(list(frame_json.keys())) if isinstance(frame_json, dict) else []
    result["frame_text_head"] = frame_text[:2500]

    p620 = frame_json.get("progress6_20_gps_yolo") if isinstance(frame_json, dict) else None
    result["progress6_20_gps_yolo"] = p620

    has_bridge = isinstance(p620, dict)
    gps_valid = bool(p620 and p620.get("gps_reliability", {}).get("gps_valid"))
    yolo_tree_detected = bool(p620 and p620.get("yolo_detection", {}).get("tree_detected"))
    yolo_status = p620.get("yolo_detection", {}).get("status") if p620 else None

    result["has_progress6_20_gps_yolo"] = has_bridge
    result["gps_valid_in_frame"] = gps_valid
    result["yolo_tree_detected_in_frame"] = yolo_tree_detected
    result["yolo_detection_status"] = yolo_status

    if frame_code < 200 or frame_code >= 300:
        result["hard_failures"].append("frame_route_failed")
    if not has_bridge:
        result["hard_failures"].append("progress6_20_bridge_key_missing")
    if not gps_valid:
        result["hard_failures"].append("gps_not_valid_in_frame_response")
    if not yolo_tree_detected:
        result["hard_failures"].append("yolo_tree_not_detected_in_frame_response")

    if not result["hard_failures"]:
        result["status"] = "PROGRESS_6_20_GPS_RELIABILITY_YOLO_DETECTION_PASS"

    write_report(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"REPORT={REPORT}")

    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())