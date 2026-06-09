from __future__ import annotations

import base64
import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import jsonify, request

try:
    import cv2
    import numpy as np
except Exception:  # pragma: no cover
    cv2 = None
    np = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TREE_MODEL_CANDIDATES = [
    PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt",
    PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt",
    PROJECT_ROOT / "models" / "field" / "tree_pohon_sono_best.pt",
]
MULTICLASS_MODEL_CANDIDATES = [
    PROJECT_ROOT / "models" / "field" / "field_multiclass_best.pt",
    PROJECT_ROOT / "runs" / "detect" / "field_multiclass_v1" / "weights" / "best.pt",
]

PROJECT_CLASS_NAMES = {"pohon_sono", "konduktor", "struktur_penyangga"}
PROJECT_CLASS_COLORS = {
    "pohon_sono": "green",
    "konduktor": "orange",
    "struktur_penyangga": "blue",
}
MULTICLASS_ALLOWED = {
    0: "struktur_penyangga",
    1: "konduktor",
    2: "pohon_sono",
}


def _now_ms() -> int:
    return int(time.time() * 1000)


def resolve_tree_model_path() -> Optional[Path]:
    for path in TREE_MODEL_CANDIDATES:
        if path.exists() and path.is_file():
            return path
    return None


def resolve_multiclass_model_path() -> Optional[Path]:
    for path in MULTICLASS_MODEL_CANDIDATES:
        if path.exists() and path.is_file():
            return path
    return None


def _safe_model_status() -> Dict[str, str]:
    tree_path = resolve_tree_model_path()
    multi_path = resolve_multiclass_model_path()
    return {
        "tree": "TREE_MODEL_READY_CANDIDATE" if tree_path else "TREE_MODEL_NOT_READY",
        "conductor": "CONDUCTOR_MODEL_NOT_READY",
        "pole": "POLE_MODEL_NOT_READY",
        "multiclass": "MULTICLASS_MODEL_READY_CANDIDATE" if multi_path else "MULTICLASS_MODEL_NOT_READY",
    }


@lru_cache(maxsize=4)
def load_yolo_model_cached(model_path: str):
    from ultralytics import YOLO
    return YOLO(model_path)


def decode_frame_base64(image_base64: str):
    if cv2 is None or np is None:
        raise RuntimeError("OPENCV_NUMPY_NOT_AVAILABLE")
    if not image_base64:
        raise ValueError("IMAGE_BASE64_EMPTY")
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    raw = base64.b64decode(image_base64, validate=False)
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("FRAME_DECODE_FAILED")
    return frame


def _bbox_norm_yxyx_1000(x1: float, y1: float, x2: float, y2: float, width: int, height: int) -> List[int]:
    if width <= 0 or height <= 0:
        return [0, 0, 0, 0]
    return [
        int(max(0, min(1000, round(y1 / height * 1000)))),
        int(max(0, min(1000, round(x1 / width * 1000)))),
        int(max(0, min(1000, round(y2 / height * 1000)))),
        int(max(0, min(1000, round(x2 / width * 1000)))),
    ]


def normalize_yolo_detection(result, frame_shape, model_kind: str = "tree") -> List[Dict[str, Any]]:
    height, width = int(frame_shape[0]), int(frame_shape[1])
    detections: List[Dict[str, Any]] = []

    names = getattr(result, "names", {}) or {}

    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return detections

    for box in boxes:
        try:
            cls_id = int(box.cls[0].item() if hasattr(box.cls[0], "item") else box.cls[0])
            conf = float(box.conf[0].item() if hasattr(box.conf[0], "item") else box.conf[0])
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = [float(v) for v in xyxy]
        except Exception:
            continue

        if model_kind == "tree":
            class_name = "pohon_sono"
            source = "YOLO_TREE_CANDIDATE"
        else:
            raw_name = str(names.get(cls_id, "")).strip()
            if cls_id in MULTICLASS_ALLOWED:
                class_name = MULTICLASS_ALLOWED[cls_id]
            elif raw_name in PROJECT_CLASS_NAMES:
                class_name = raw_name
            else:
                class_name = raw_name or f"class_{cls_id}"
            source = "YOLO_MULTICLASS_CANDIDATE"

        detections.append(
            {
                "class_id": cls_id,
                "class_name": class_name,
                "object_group": class_name,
                "confidence": round(conf, 4),
                "bbox_xyxy_px": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "bbox_norm_yxyx_1000": _bbox_norm_yxyx_1000(x1, y1, x2, y2, width, height),
                "bbox_color": PROJECT_CLASS_COLORS.get(class_name, "gray"),
                "source": source,
            }
        )

    return detections


def filter_project_classes_only(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for det in detections or []:
        class_name = str(det.get("class_name") or "").strip()
        if class_name in PROJECT_CLASS_NAMES:
            out.append(det)
    return out


def run_tree_yolo_candidate(frame, conf: float = 0.25, iou: float = 0.5, max_det: int = 8) -> Tuple[str, List[Dict[str, Any]]]:
    tree_path = resolve_tree_model_path()
    if not tree_path:
        return "TREE_MODEL_NOT_READY", []

    try:
        model = load_yolo_model_cached(str(tree_path))
        results = model.predict(source=frame, conf=conf, iou=iou, imgsz=640, max_det=max_det, verbose=False)
        if not results:
            return "TREE_MODEL_READY_CANDIDATE_NO_DETECTION", []
        detections = normalize_yolo_detection(results[0], frame.shape, model_kind="tree")
        detections = filter_project_classes_only(detections)
        if detections:
            return "TREE_DETECTED_CANDIDATE", detections
        return "TREE_MODEL_READY_CANDIDATE_NO_DETECTION", []
    except Exception as exc:
        return f"TREE_MODEL_RUNTIME_ERROR:{type(exc).__name__}", []


def run_multiclass_yolo_if_ready(frame, conf: float = 0.25, iou: float = 0.5, max_det: int = 12) -> Tuple[str, List[Dict[str, Any]]]:
    multi_path = resolve_multiclass_model_path()
    if not multi_path:
        return "MULTICLASS_MODEL_NOT_READY", []

    try:
        model = load_yolo_model_cached(str(multi_path))
        names = getattr(model, "names", {}) or {}
        names_joined = " ".join(str(v) for v in names.values()).lower()
        expected_tokens = ["struktur", "konduktor", "pohon"]
        if not all(token in names_joined for token in expected_tokens):
            return "MULTICLASS_MODEL_PRESENT_CLASS_ORDER_UNVERIFIED", []

        results = model.predict(source=frame, conf=conf, iou=iou, imgsz=640, max_det=max_det, verbose=False)
        if not results:
            return "MULTICLASS_READY_NO_DETECTION", []
        detections = normalize_yolo_detection(results[0], frame.shape, model_kind="multiclass")
        detections = filter_project_classes_only(detections)
        if detections:
            return "MULTICLASS_PROJECT_OBJECT_DETECTED", detections
        return "MULTICLASS_READY_NO_PROJECT_CLASS_DETECTION", []
    except Exception as exc:
        return f"MULTICLASS_MODEL_RUNTIME_ERROR:{type(exc).__name__}", []


def classify_runtime_detection_status(detections: List[Dict[str, Any]], readiness: Dict[str, str]) -> str:
    if detections:
        groups = {d.get("class_name") for d in detections}
        if "pohon_sono" in groups and ("konduktor" in groups or "struktur_penyangga" in groups):
            return "PROJECT_PARTIAL_MULTI_OBJECT_DETECTED"
        if "pohon_sono" in groups:
            return "TREE_DETECTED_CANDIDATE"
        return "PROJECT_OBJECT_DETECTED"
    if readiness.get("tree") == "TREE_MODEL_READY_CANDIDATE":
        return "YOLO_READY_NO_PROJECT_DETECTION"
    return "MODEL_NOT_READY_SAFE_MODE"


def _float_or_none(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _build_prediction(payload: Dict[str, Any], detections: List[Dict[str, Any]], models: Dict[str, str]) -> Dict[str, Any]:
    classes = {str(d.get("class_name")) for d in detections}
    clearance_m = _float_or_none(payload.get("clearance_m"))
    growth_rate = _float_or_none(payload.get("growth_rate_m_per_day") or payload.get("growth_rate"))
    threshold = 3.0

    regression_status = "GROWTH_LINEAR_REGRESSION_READY_PROXY_DATASET"
    source_status = "PROXY_NOT_FIELD_OBSERVED"

    if clearance_m is None:
        if "pohon_sono" in classes:
            return {
                "object_status": "TREE_DETECTED_CANDIDATE",
                "clearance_status": "CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR",
                "eta_status": "INSUFFICIENT_GEOMETRY_DATA",
                "risk_status": "EVIDENCE_ONLY",
                "regression_status": regression_status,
                "source_status": source_status,
                "display_summary": "Pohon terdeteksi kandidat. Clearance dan ETA belum final karena konduktor/struktur/kalibrasi belum cukup.",
                "limitations": ["NO_FINAL_POLE_CONDUCTOR_MODEL", "NO_VALID_CLEARANCE_GEOMETRY"],
            }
        return {
            "object_status": "NO_PROJECT_OBJECT_DETECTED",
            "clearance_status": "CLEARANCE_NOT_AVAILABLE",
            "eta_status": "INSUFFICIENT_GEOMETRY_DATA",
            "risk_status": "EVIDENCE_ONLY",
            "regression_status": regression_status,
            "source_status": source_status,
            "display_summary": "Belum ada objek inti project yang valid pada frame ini.",
            "limitations": ["NO_PROJECT_OBJECT_DETECTED"],
        }

    if clearance_m <= threshold:
        eta_days = 0
        risk = "ACTION_REQUIRED"
        eta_status = "ETA_ZERO_CLEARANCE_AT_OR_BELOW_THRESHOLD"
    elif growth_rate is not None and growth_rate > 0:
        eta_days = int(round((clearance_m - threshold) / growth_rate))
        risk = "MONITORING_REQUIRED" if eta_days <= 180 else "TEMPORARILY_SAFE_MONITOR"
        eta_status = "ETA_PROVISIONAL_FROM_REGRESSION_PROXY"
    else:
        eta_days = None
        risk = "EVIDENCE_ONLY"
        eta_status = "INSUFFICIENT_GROWTH_RATE_DATA"

    return {
        "object_status": "TREE_DETECTED_CANDIDATE" if "pohon_sono" in classes else "OBJECT_EVIDENCE_ONLY",
        "clearance_m": clearance_m,
        "clearance_threshold_m": threshold,
        "clearance_status": "CLEARANCE_MANUAL_PROVISIONAL" if clearance_m is not None else "CLEARANCE_NOT_AVAILABLE",
        "eta_days": eta_days,
        "eta_status": eta_status,
        "risk_status": risk,
        "regression_status": regression_status,
        "source_status": source_status,
        "display_summary": f"Clearance {clearance_m:.2f} m, status {risk}, ETA {eta_days if eta_days is not None else 'belum cukup data'}.",
        "limitations": ["MANUAL_OR_PROXY_GEOMETRY_NOT_FINAL"],
    }


def _make_safe_response(
    session_id: str,
    status: str,
    detections: Optional[List[Dict[str, Any]]] = None,
    prediction: Optional[Dict[str, Any]] = None,
    started_ms: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    models = _safe_model_status()
    latency_ms = max(0, _now_ms() - (started_ms or _now_ms()))
    payload = {
        "ok": True,
        "status": status,
        "runtime_mode": "YOLO_FIRST",
        "session_id": session_id,
        "frame_id": f"F{_now_ms()}",
        "latency_ms": latency_ms,
        "refresh_contract_ms": 1000,
        "models": models,
        "detections": detections or [],
        "prediction": prediction or {
            "clearance_status": "CLEARANCE_NOT_AVAILABLE",
            "eta_status": "INSUFFICIENT_GEOMETRY_DATA",
            "risk_status": "EVIDENCE_ONLY",
            "regression_status": "NOT_AVAILABLE",
            "display_summary": "Prediction belum tersedia.",
        },
        "no_fake_detection": True,
        "no_fake_clearance": True,
        "no_fake_gps": True,
    }
    if extra:
        payload.update(extra)
    return jsonify(payload), 200


def _progress626_frame_handler():
    started = _now_ms()
    payload = request.get_json(silent=True) or {}
    session_id = str(payload.get("session_id") or "").strip()

    if not session_id:
        return _make_safe_response(
            session_id="",
            status="FIELD_SESSION_ID_REQUIRED",
            detections=[],
            prediction={
                "clearance_status": "CLEARANCE_NOT_AVAILABLE",
                "eta_status": "INSUFFICIENT_GEOMETRY_DATA",
                "risk_status": "EVIDENCE_ONLY",
                "regression_status": "NOT_AVAILABLE",
                "display_summary": "Session ID kosong.",
            },
            started_ms=started,
        )

    if payload.get("ai_switch_on") is False:
        try:
            from ulp_project.realtime_project_tracker import reset_tracks
            reset_tracks(session_id)
        except Exception:
            pass
        return _make_safe_response(
            session_id=session_id,
            status="YOLO_REALTIME_SWITCH_OFF_TRACKS_RESET",
            detections=[],
            prediction={
                "clearance_status": "REALTIME_OFF",
                "eta_status": "REALTIME_OFF",
                "risk_status": "EVIDENCE_ONLY",
                "regression_status": "NOT_AVAILABLE",
                "display_summary": "Realtime OFF. Overlay dibersihkan.",
            },
            started_ms=started,
        )

    try:
        frame = decode_frame_base64(str(payload.get("image_base64") or ""))
    except Exception as exc:
        prediction = _build_prediction(payload, [], _safe_model_status())
        return _make_safe_response(
            session_id=session_id,
            status=f"FRAME_DECODE_FAILED:{type(exc).__name__}",
            detections=[],
            prediction=prediction,
            started_ms=started,
        )

    models = _safe_model_status()
    detections: List[Dict[str, Any]] = []
    status_parts: List[str] = []

    multi_status, multi_det = run_multiclass_yolo_if_ready(frame, conf=0.25, iou=0.5, max_det=12)
    status_parts.append(multi_status)
    detections.extend(multi_det)

    if not any(d.get("class_name") == "pohon_sono" for d in detections):
        tree_status, tree_det = run_tree_yolo_candidate(frame, conf=0.25, iou=0.5, max_det=8)
        status_parts.append(tree_status)
        detections.extend(tree_det)

    detections = filter_project_classes_only(detections)

    try:
        from ulp_project.realtime_project_tracker import assign_stable_track_ids
        detections = assign_stable_track_ids(detections, session_id=session_id, max_lost_frames=8)
    except Exception:
        for idx, det in enumerate(detections):
            det["track_id"] = idx + 1
            det["track_status"] = "TRACKER_FALLBACK_NOT_AVAILABLE"

    runtime_status = classify_runtime_detection_status(detections, models)
    prediction = _build_prediction(payload, detections, models)

    return _make_safe_response(
        session_id=session_id,
        status=runtime_status,
        detections=detections,
        prediction=prediction,
        started_ms=started,
        extra={
            "status_detail": status_parts,
            "project_classes_only": True,
            "cloud_vision_core_loop": False,
        },
    )


def _progress626_status_handler():
    tree_path = resolve_tree_model_path()
    multi_path = resolve_multiclass_model_path()
    return jsonify(
        {
            "ok": True,
            "status": "PROGRESS_6_26_YOLO_FIRST_RUNTIME_READY",
            "runtime_mode": "YOLO_FIRST",
            "frame_endpoint": "/api/field/session/frame",
            "vision_analyze_core_loop": False,
            "tree_model_path": str(tree_path) if tree_path else None,
            "multiclass_model_path": str(multi_path) if multi_path else None,
            "models": _safe_model_status(),
            "project_classes": ["struktur_penyangga", "konduktor", "pohon_sono"],
            "no_fake_detection": True,
            "no_fake_clearance": True,
            "no_fake_gps": True,
        }
    ), 200


def register_progress6_26_yolo_first(app):
    frame_rule = "/api/field/session/frame"
    status_rule = "/api/runtime/progress6-26-yolo-first-status"

    existing_frame_endpoint = None
    existing_status_endpoint = None

    try:
        for rule in app.url_map.iter_rules():
            if rule.rule == frame_rule and "POST" in rule.methods:
                existing_frame_endpoint = rule.endpoint
            if rule.rule == status_rule and "GET" in rule.methods:
                existing_status_endpoint = rule.endpoint
    except Exception:
        existing_frame_endpoint = None
        existing_status_endpoint = None

    if existing_frame_endpoint:
        app.view_functions[existing_frame_endpoint] = _progress626_frame_handler
    else:
        app.add_url_rule(
            frame_rule,
            endpoint="progress6_26_field_session_frame",
            view_func=_progress626_frame_handler,
            methods=["POST"],
        )

    if existing_status_endpoint:
        app.view_functions[existing_status_endpoint] = _progress626_status_handler
    else:
        app.add_url_rule(
            status_rule,
            endpoint="progress6_26_yolo_first_status",
            view_func=_progress626_status_handler,
            methods=["GET"],
        )

    app.config["PROGRESS_6_26_YOLO_FIRST_REGISTERED"] = True
    return app
