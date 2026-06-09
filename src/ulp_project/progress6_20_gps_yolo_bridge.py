from __future__ import annotations

import base64
import json
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import jsonify, make_response, request

VERSION = "progress6_20_gps_yolo_bridge"
ROOT = Path(__file__).resolve().parents[2]

GPS_STORE: Dict[str, Dict[str, Any]] = {}
MODEL_LOCK = threading.Lock()
YOLO_MODEL = None
YOLO_MODEL_PATH: Optional[Path] = None

MODEL_CANDIDATES = [
    ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt",
    ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt",
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _find_model_path() -> Optional[Path]:
    for path in MODEL_CANDIDATES:
        if path.exists():
            return path
    return None


def _load_model():
    global YOLO_MODEL, YOLO_MODEL_PATH

    with MODEL_LOCK:
        if YOLO_MODEL is not None:
            return YOLO_MODEL, YOLO_MODEL_PATH

        model_path = _find_model_path()
        YOLO_MODEL_PATH = model_path

        if model_path is None:
            YOLO_MODEL = None
            return None, None

        from ultralytics import YOLO

        YOLO_MODEL = YOLO(str(model_path))
        return YOLO_MODEL, model_path


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return float(value)
    except Exception:
        return None


def _valid_lat_lon(lat: Any, lon: Any) -> bool:
    lat_f = _safe_float(lat)
    lon_f = _safe_float(lon)
    if lat_f is None or lon_f is None:
        return False
    return -90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0


def _extract_session_id(payload: Any = None) -> str:
    candidates: List[Any] = []

    if payload is not None:
        if isinstance(payload, dict):
            candidates.extend([
                payload.get("session_id"),
                payload.get("sessionId"),
                payload.get("field_session_id"),
            ])

    try:
        candidates.extend([
            request.args.get("session_id"),
            request.args.get("sessionId"),
            request.form.get("session_id"),
        ])
    except Exception:
        pass

    for value in candidates:
        if isinstance(value, str) and value.startswith("FS_"):
            return value.strip()

    try:
        text = request.get_data(as_text=True) or ""
        match = re.search(r"FS_\d{8}_\d{6}_[A-Za-z0-9]+", text)
        if match:
            return match.group(0)
    except Exception:
        pass

    return ""


def _deep_get(d: Any, path: List[str]) -> Any:
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _extract_gps(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "valid": False,
            "status": "GPS_PAYLOAD_NOT_OBJECT",
            "reason": "GPS payload is not JSON object",
        }

    lat_candidates = [
        payload.get("latitude"),
        payload.get("lat"),
        _deep_get(payload, ["gps", "latitude"]),
        _deep_get(payload, ["gps", "lat"]),
        _deep_get(payload, ["coords", "latitude"]),
        _deep_get(payload, ["coords", "lat"]),
        _deep_get(payload, ["current_gps", "latitude"]),
        _deep_get(payload, ["base_gps", "latitude"]),
    ]

    lon_candidates = [
        payload.get("longitude"),
        payload.get("lon"),
        payload.get("lng"),
        _deep_get(payload, ["gps", "longitude"]),
        _deep_get(payload, ["gps", "lon"]),
        _deep_get(payload, ["gps", "lng"]),
        _deep_get(payload, ["coords", "longitude"]),
        _deep_get(payload, ["coords", "lon"]),
        _deep_get(payload, ["coords", "lng"]),
        _deep_get(payload, ["current_gps", "longitude"]),
        _deep_get(payload, ["current_gps", "lon"]),
        _deep_get(payload, ["base_gps", "longitude"]),
        _deep_get(payload, ["base_gps", "lon"]),
    ]

    acc_candidates = [
        payload.get("accuracy"),
        payload.get("accuracy_m"),
        payload.get("gps_accuracy_m"),
        _deep_get(payload, ["gps", "accuracy"]),
        _deep_get(payload, ["gps", "gps_accuracy_m"]),
        _deep_get(payload, ["coords", "accuracy"]),
        _deep_get(payload, ["current_gps", "accuracy"]),
        _deep_get(payload, ["base_gps", "accuracy"]),
    ]

    lat = next((x for x in lat_candidates if _safe_float(x) is not None), None)
    lon = next((x for x in lon_candidates if _safe_float(x) is not None), None)
    acc = next((x for x in acc_candidates if _safe_float(x) is not None), None)

    if not _valid_lat_lon(lat, lon):
        return {
            "valid": False,
            "status": "GPS_COORDINATE_INVALID_OR_TIMEOUT",
            "reason": "Latitude/longitude missing or invalid",
            "lat": None,
            "lon": None,
            "accuracy_m": None,
            "source": payload.get("source") or payload.get("gps_source") or "UNKNOWN",
        }

    acc_f = _safe_float(acc)
    if acc_f is None:
        acc_f = -1.0

    lat_f = float(lat)
    lon_f = float(lon)

    status = "GPS_READY"
    if acc_f >= 0:
        if acc_f <= 10:
            status = "GPS_READY_HIGH_CONFIDENCE"
        elif acc_f <= 25:
            status = "GPS_READY_MEDIUM_CONFIDENCE"
        else:
            status = "GPS_READY_LOW_CONFIDENCE"

    return {
        "valid": True,
        "status": status,
        "lat": lat_f,
        "lon": lon_f,
        "accuracy_m": acc_f,
        "source": payload.get("source") or payload.get("gps_source") or "BROWSER_OR_OPERATOR_GPS",
        "updated_at": _now(),
    }


def _extract_frame_base64(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""

    keys = [
        "frame_base64",
        "image_base64",
        "jpeg_base64",
        "frame",
        "image",
        "snapshot_base64",
        "camera_frame_base64",
    ]

    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and len(value) > 100:
            if "," in value and value.strip().startswith("data:"):
                return value.split(",", 1)[1]
            return value.strip()

    return ""


def _decode_frame(payload: Any) -> Tuple[bool, str, Any]:
    frame_b64 = _extract_frame_base64(payload)
    if not frame_b64:
        return False, "FRAME_BASE64_NOT_FOUND", None

    try:
        import cv2
        import numpy as np

        raw = base64.b64decode(frame_b64, validate=False)
        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return False, "FRAME_DECODE_FAILED", None
        return True, "FRAME_DECODE_OK", img
    except Exception as exc:
        return False, f"FRAME_DECODE_EXCEPTION: {exc}", None


def _run_yolo_on_frame(img: Any) -> Dict[str, Any]:
    model, model_path = _load_model()

    if model is None or model_path is None:
        return {
            "status": "TREE_MODEL_NOT_FOUND",
            "model_status": "TREE_MODEL_NOT_READY",
            "model_path": None,
            "tree_detected": False,
            "detection_count": 0,
            "track_id_seen": False,
            "tree_track_ids": [],
            "detections": [],
            "no_fake_detection": True,
        }

    try:
        results = None
        tracker_used = "bytetrack.yaml"

        try:
            results = model.track(
                source=img,
                persist=True,
                tracker=tracker_used,
                conf=0.25,
                verbose=False,
            )
        except Exception:
            tracker_used = "predict_fallback"
            results = model.predict(
                source=img,
                conf=0.25,
                verbose=False,
            )

        detections: List[Dict[str, Any]] = []
        track_ids: List[int] = []
        names = getattr(model, "names", {}) or {}

        for result in results or []:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            xyxy_obj = getattr(boxes, "xyxy", None)
            cls_obj = getattr(boxes, "cls", None)
            conf_obj = getattr(boxes, "conf", None)
            id_obj = getattr(boxes, "id", None)

            xyxy = xyxy_obj.cpu().numpy().tolist() if xyxy_obj is not None else []
            cls_list = cls_obj.cpu().numpy().tolist() if cls_obj is not None else []
            conf_list = conf_obj.cpu().numpy().tolist() if conf_obj is not None else []
            id_list = id_obj.cpu().numpy().tolist() if id_obj is not None else [None] * len(xyxy)

            for idx, box in enumerate(xyxy):
                cls_id = int(cls_list[idx]) if idx < len(cls_list) else 0
                conf = float(conf_list[idx]) if idx < len(conf_list) else 0.0
                cls_name = str(names.get(cls_id, cls_id))
                track_id = id_list[idx] if idx < len(id_list) else None

                det = {
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": round(conf, 4),
                    "bbox_xyxy": [round(float(v), 2) for v in box],
                    "track_id": int(track_id) if track_id is not None else None,
                }
                detections.append(det)

                if track_id is not None:
                    try:
                        track_ids.append(int(track_id))
                    except Exception:
                        pass

        tree_detections = [
            d for d in detections
            if d.get("class_id") == 0 or str(d.get("class_name", "")).lower() in {"pohon_sono", "tree_sono", "sono"}
        ]

        tree_detected = len(tree_detections) > 0
        track_id_seen = len(track_ids) > 0

        return {
            "status": "YOLO_TREE_DETECTED" if tree_detected else "YOLO_READY_NO_TREE_DETECTED",
            "model_status": "TREE_MODEL_READY_CANDIDATE",
            "model_path": str(model_path.relative_to(ROOT)),
            "tracker": tracker_used,
            "tree_detected": tree_detected,
            "detection_count": len(tree_detections),
            "total_detection_count": len(detections),
            "track_id_seen": track_id_seen,
            "tree_track_ids": sorted(list(set(track_ids))),
            "detections": tree_detections,
            "no_fake_detection": True,
            "note": "Deteksi hanya sah jika frame berisi pohon_sono; tidak ada fake detection.",
        }
    except Exception as exc:
        return {
            "status": "YOLO_RUNTIME_EXCEPTION",
            "model_status": "TREE_MODEL_READY_CANDIDATE",
            "model_path": str(model_path.relative_to(ROOT)),
            "tree_detected": False,
            "detection_count": 0,
            "track_id_seen": False,
            "tree_track_ids": [],
            "detections": [],
            "no_fake_detection": True,
            "exception": repr(exc),
        }


def _response_json(response) -> Optional[Dict[str, Any]]:
    try:
        text = response.get_data(as_text=True)
        if not text:
            return None
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _find_endpoint(app, rule_path: str) -> Optional[str]:
    for rule in app.url_map.iter_rules():
        if str(rule.rule) == rule_path:
            return rule.endpoint
    return None


def install_progress6_20_gps_yolo_bridge(app):
    if app.config.get("_PROGRESS_6_20_GPS_YOLO_INSTALLED"):
        return app

    app.config["_PROGRESS_6_20_GPS_YOLO_INSTALLED"] = True

    gps_endpoint = _find_endpoint(app, "/api/field/session/gps-update")
    frame_endpoint = _find_endpoint(app, "/api/field/session/frame")

    if gps_endpoint and gps_endpoint in app.view_functions:
        original_gps = app.view_functions[gps_endpoint]

        def progress6_20_gps_update_wrapper(*args, **kwargs):
            payload = request.get_json(silent=True) or {}
            session_id = _extract_session_id(payload)
            gps = _extract_gps(payload)

            if session_id and gps.get("valid"):
                GPS_STORE[session_id] = gps

            original_response = make_response(original_gps(*args, **kwargs))
            data = _response_json(original_response)

            reliability = {
                "version": VERSION,
                "session_id": session_id,
                "gps_valid": bool(gps.get("valid")),
                "gps_status": gps.get("status"),
                "gps": gps,
                "cached_for_session": bool(session_id and session_id in GPS_STORE),
                "no_fake_coordinate": True,
            }

            if data is not None:
                data["progress6_20_gps_reliability"] = reliability
                return jsonify(data), original_response.status_code

            return original_response

        app.view_functions[gps_endpoint] = progress6_20_gps_update_wrapper

    if frame_endpoint and frame_endpoint in app.view_functions:
        original_frame = app.view_functions[frame_endpoint]

        def progress6_20_frame_wrapper(*args, **kwargs):
            payload = request.get_json(silent=True) or {}
            session_id = _extract_session_id(payload)

            original_response = make_response(original_frame(*args, **kwargs))
            data = _response_json(original_response)

            if data is None:
                data = {
                    "original_response_non_json": original_response.get_data(as_text=True)[:1500],
                    "status": "ORIGINAL_FRAME_RESPONSE_NON_JSON",
                }

            session_id = session_id or str(data.get("session_id") or "")
            gps_cached = GPS_STORE.get(session_id) if session_id else None

            decode_ok, decode_status, img = _decode_frame(payload)
            if decode_ok:
                yolo = _run_yolo_on_frame(img)
            else:
                yolo = {
                    "status": "FRAME_NOT_AVAILABLE_FOR_YOLO",
                    "model_status": "TREE_MODEL_READY_CANDIDATE" if _find_model_path() else "TREE_MODEL_NOT_READY",
                    "tree_detected": False,
                    "detection_count": 0,
                    "track_id_seen": False,
                    "tree_track_ids": [],
                    "detections": [],
                    "no_fake_detection": True,
                    "decode_status": decode_status,
                }

            gps_reliability = {
                "status": gps_cached.get("status") if gps_cached else "GPS_PENDING_OR_TIMEOUT_NO_FAKE_COORDINATE",
                "gps_valid": bool(gps_cached),
                "gps": gps_cached,
                "session_id": session_id,
                "no_fake_coordinate": True,
                "note": "GPS tidak memblokir YOLO; GPS hanya evidence lokasi.",
            }

            merged_status = "GPS_AND_YOLO_READY"
            if not gps_cached and yolo.get("tree_detected"):
                merged_status = "YOLO_READY_GPS_PENDING"
            elif gps_cached and not yolo.get("tree_detected"):
                merged_status = "GPS_READY_YOLO_NO_TREE_DETECTED"
            elif not gps_cached and not yolo.get("tree_detected"):
                merged_status = "GPS_PENDING_YOLO_NO_TREE_DETECTED"

            progress = {
                "version": VERSION,
                "session_id": session_id,
                "merged_status": merged_status,
                "gps_reliability": gps_reliability,
                "yolo_detection": yolo,
                "monocular_scaling_status": "NOT_STARTED_WAITING_FOR_YOLO_AND_REFERENCE_GEOMETRY",
                "clearance_status": "CLEARANCE_NOT_FINAL_MONO_SCALING_NOT_STARTED",
                "eta_status": "ETA_NOT_FINAL_MONO_SCALING_NOT_STARTED",
                "no_fake_detection": True,
                "no_fake_coordinate": True,
                "no_label_touch": True,
                "no_raw_touch": True,
                "no_dataset_touch": True,
                "no_runs_touch": True,
                "no_weights_touch": True,
            }

            data["progress6_20_gps_yolo"] = progress
            data["gps_reliability_status"] = gps_reliability["status"]
            data["yolo_detection_status"] = yolo.get("status")
            data["runtime_gps_yolo_integrated"] = True

            if yolo.get("tree_detected"):
                data["tree_detected"] = True
                data["tree_model_status"] = "TREE_MODEL_READY_CANDIDATE"
                data["model_status"] = "TREE_MODEL_READY_CANDIDATE"
                data["detections"] = yolo.get("detections", [])
                data["detected_classes"] = ["pohon_sono"]
                data["tree_confidence"] = max([float(d.get("confidence", 0.0)) for d in yolo.get("detections", [])] or [0.0])
                data["tracking_status"] = yolo.get("status")
                data["track_id_seen"] = yolo.get("track_id_seen", False)
                data["tree_track_ids"] = yolo.get("tree_track_ids", [])

            try:
                from ulp_project.live_yolo_canonical_output import build_live_yolo_canonical_output
                data = build_live_yolo_canonical_output(data)
            except Exception as exc:
                data["canonical_yolo_output_status"] = "PROGRESS_6_21_CANONICAL_OUTPUT_FAILED_SAFE"
                data["canonical_yolo_output_error"] = repr(exc)
                data["no_fake_detection"] = True
                data["no_fake_pole_conductor_detection"] = True

            return jsonify(data), original_response.status_code

        app.view_functions[frame_endpoint] = progress6_20_frame_wrapper

    def progress6_20_status():
        model_path = _find_model_path()
        return jsonify({
            "version": VERSION,
            "status": "PROGRESS_6_20_GPS_YOLO_BRIDGE_INSTALLED",
            "gps_endpoint": gps_endpoint,
            "frame_endpoint": frame_endpoint,
            "gps_route_wrapped": bool(gps_endpoint),
            "frame_route_wrapped": bool(frame_endpoint),
            "gps_cached_session_count": len(GPS_STORE),
            "tree_model_status": "TREE_MODEL_READY_CANDIDATE" if model_path else "TREE_MODEL_NOT_READY",
            "tree_model_path": str(model_path.relative_to(ROOT)) if model_path else None,
            "monocular_scaling_status": "NOT_STARTED",
            "no_fake_detection": True,
            "no_fake_coordinate": True,
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
        })

    endpoint_name = "progress6_20_gps_yolo_status"
    if endpoint_name not in app.view_functions:
        app.add_url_rule(
            "/api/runtime/progress6-20-gps-yolo-status",
            endpoint=endpoint_name,
            view_func=progress6_20_status,
            methods=["GET"],
        )

    return app
