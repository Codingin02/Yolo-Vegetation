from __future__ import annotations

import base64
import json
import math
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
TREE_MODEL_PATH = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _clip_box_xyxy(box: List[float], width: int, height: int) -> Optional[List[int]]:
    if len(box) < 4:
        return None

    x1 = int(max(0, min(width - 1, round(float(box[0])))))
    y1 = int(max(0, min(height - 1, round(float(box[1])))))
    x2 = int(max(0, min(width - 1, round(float(box[2])))))
    y2 = int(max(0, min(height - 1, round(float(box[3])))))

    if x2 <= x1 or y2 <= y1:
        return None

    return [x1, y1, x2, y2]


def decode_frame_base64(value: str) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
    info: Dict[str, Any] = {
        "ok": False,
        "status": "FRAME_NOT_DECODED",
        "height": None,
        "width": None,
        "used_data_url": False,
    }

    if not isinstance(value, str) or not value.strip():
        info["status"] = "FRAME_BASE64_EMPTY"
        return None, info

    raw = value.strip()

    if "," in raw and raw.lower().startswith("data:image"):
        raw = raw.split(",", 1)[1]
        info["used_data_url"] = True

    try:
        binary = base64.b64decode(raw, validate=False)
        arr = np.frombuffer(binary, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as exc:
        info["status"] = f"FRAME_DECODE_EXCEPTION:{type(exc).__name__}"
        return None, info

    if frame is None:
        info["status"] = "FRAME_DECODE_FAILED"
        return None, info

    h, w = frame.shape[:2]
    info.update({"ok": True, "status": "FRAME_DECODE_OK", "height": h, "width": w})
    return frame, info


@dataclass
class TrackState:
    track_id: int
    class_name: str
    class_id: int
    confidence: float
    bbox_xyxy: List[int]
    center_xy: Tuple[float, float]
    first_seen_frame: int
    last_seen_frame: int
    age_frames: int = 1
    missed_frames: int = 0


class SimpleIoUTracker:
    """
    Tracker ringan untuk runtime field-smoke.
    Tujuan: stabilkan ID antar frame tanpa menambah dependency baru.
    Ini bukan pengganti final ByteTrack, tetapi bridge aman sampai tracking final live dipaketkan.
    """

    def __init__(self, iou_threshold: float = 0.25, max_missed: int = 8) -> None:
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self.next_id = 1
        self.tracks: Dict[int, TrackState] = {}

    @staticmethod
    def iou(a: List[int], b: List[int]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b

        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        iw = max(0, ix2 - ix1)
        ih = max(0, iy2 - iy1)
        inter = iw * ih

        aa = max(1, (ax2 - ax1) * (ay2 - ay1))
        ba = max(1, (bx2 - bx1) * (by2 - by1))

        return inter / float(aa + ba - inter)

    def update(self, detections: List[Dict[str, Any]], frame_index: int) -> Dict[str, Any]:
        assigned_tracks: set[int] = set()
        assigned_detections: set[int] = set()
        output: List[Dict[str, Any]] = []

        for det_idx, det in enumerate(detections):
            bbox = det.get("bbox_xyxy")
            if not bbox:
                continue

            best_track_id = None
            best_iou = 0.0

            for track_id, track in self.tracks.items():
                if track_id in assigned_tracks:
                    continue
                if track.class_id != int(det.get("class_id", -999)):
                    continue

                score = self.iou(track.bbox_xyxy, bbox)
                if score > best_iou:
                    best_iou = score
                    best_track_id = track_id

            if best_track_id is not None and best_iou >= self.iou_threshold:
                track = self.tracks[best_track_id]
                track.bbox_xyxy = bbox
                track.center_xy = det["center_xy"]
                track.confidence = float(det.get("confidence", 0.0))
                track.last_seen_frame = frame_index
                track.age_frames += 1
                track.missed_frames = 0

                assigned_tracks.add(best_track_id)
                assigned_detections.add(det_idx)

                item = dict(det)
                item["track_id"] = best_track_id
                item["track_iou"] = round(best_iou, 4)
                output.append(item)

        for det_idx, det in enumerate(detections):
            if det_idx in assigned_detections:
                continue

            track_id = self.next_id
            self.next_id += 1

            track = TrackState(
                track_id=track_id,
                class_name=str(det.get("class_name", "object")),
                class_id=int(det.get("class_id", -1)),
                confidence=float(det.get("confidence", 0.0)),
                bbox_xyxy=list(det.get("bbox_xyxy", [])),
                center_xy=tuple(det.get("center_xy", (0.0, 0.0))),
                first_seen_frame=frame_index,
                last_seen_frame=frame_index,
            )
            self.tracks[track_id] = track

            item = dict(det)
            item["track_id"] = track_id
            item["track_iou"] = None
            output.append(item)

        for track_id, track in list(self.tracks.items()):
            if track_id not in assigned_tracks and track.last_seen_frame != frame_index:
                track.missed_frames += 1
                if track.missed_frames > self.max_missed:
                    del self.tracks[track_id]

        return {
            "tracking_status": "TRACKING_READY_WITH_DETECTIONS" if output else "TRACKING_READY_NO_DETECTION",
            "track_id_seen": any(item.get("track_id") is not None for item in output),
            "active_track_count": len(self.tracks),
            "tracked_detections": output,
            "tracker_backend": "SIMPLE_IOU_TRACKER_SAFE_BRIDGE",
            "tracker_note": "Bridge runtime; ByteTrack/BoT-SORT tetap target lanjutan jika live detection sudah stabil.",
        }


_TRACKER = SimpleIoUTracker()
_FRAME_INDEX = 0


def _detect_green_synthetic_target(frame: np.ndarray) -> List[Dict[str, Any]]:
    """
    Diagnostic-only detector untuk smoke synthetic frame.
    Tidak dipakai sebagai fake detection lapangan. Hanya aktif ketika frame diberi marker synthetic.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (35, 35, 20), (95, 255, 255))
    mask = cv2.medianBlur(mask, 5)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detections: List[Dict[str, Any]] = []
    h, w = frame.shape[:2]

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < 900:
            continue

        x, y, bw, bh = cv2.boundingRect(contour)
        box = _clip_box_xyxy([x, y, x + bw, y + bh], w, h)
        if box is None:
            continue

        cx = (box[0] + box[2]) / 2.0
        cy = (box[1] + box[3]) / 2.0

        detections.append(
            {
                "class_id": 0,
                "class_name": "pohon_sono",
                "label": "pohon_sono",
                "confidence": 0.99,
                "bbox_xyxy": box,
                "center_xy": (cx, cy),
                "source": "SYNTHETIC_SMOKE_DIAGNOSTIC_ONLY",
                "no_fake_field_detection": True,
            }
        )

    return detections[:5]


def edge_refinement_diagnostic(frame: np.ndarray, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    if frame is None:
        return {
            "edge_status": "EDGE_NOT_AVAILABLE_NO_FRAME",
            "edge_refinement_final": False,
            "items": [],
        }

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 60, 160)

    h, w = frame.shape[:2]
    items: List[Dict[str, Any]] = []

    for det in detections:
        box = _clip_box_xyxy(det.get("bbox_xyxy", []), w, h)
        if box is None:
            continue

        x1, y1, x2, y2 = box
        roi = edges[y1:y2, x1:x2]
        roi_area = max(1, roi.shape[0] * roi.shape[1])
        edge_pixels = int(np.count_nonzero(roi))
        edge_ratio = edge_pixels / float(roi_area)

        items.append(
            {
                "track_id": det.get("track_id"),
                "class_name": det.get("class_name"),
                "bbox_xyxy": box,
                "edge_pixels": edge_pixels,
                "edge_ratio": round(edge_ratio, 6),
                "edge_status": "EDGE_DIAGNOSTIC_READY",
                "edge_refinement_final": False,
                "limitation": "Edge hanya diagnostic batas visual, bukan bukti clearance final.",
            }
        )

    return {
        "edge_status": "EDGE_DIAGNOSTIC_READY" if items else "EDGE_READY_NO_DETECTION",
        "edge_refinement_final": False,
        "items": items,
    }


def measurement_guard(
    detections: List[Dict[str, Any]],
    manual_reference: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    manual_reference = manual_reference or {}

    has_tree = any(str(d.get("class_name")) in {"pohon_sono", "tree_sono", "tree"} for d in detections)
    has_conductor = any(str(d.get("class_name")) in {"konduktor", "conductor"} for d in detections)
    has_pole = any(str(d.get("class_name")) in {"struktur_penyangga", "support_structure", "pole"} for d in detections)

    reference_height_m = _safe_float(manual_reference.get("reference_height_m"))
    reference_pixel_height = _safe_float(manual_reference.get("reference_pixel_height"))

    reference_valid = (
        reference_height_m is not None
        and reference_pixel_height is not None
        and reference_height_m > 0
        and reference_pixel_height > 0
    )

    if not has_tree:
        return {
            "measurement_status": "MEASUREMENT_NOT_READY_NO_TREE_DETECTION",
            "clearance_status": "CLEARANCE_NOT_FINAL",
            "eta_status": "ETA_NOT_FINAL",
            "meter_per_px": None,
            "reason_codes": ["NO_TREE_DETECTION"],
            "no_fake_clearance": True,
        }

    if not has_conductor or not has_pole:
        return {
            "measurement_status": "MEASUREMENT_BLOCKED_NO_POLE_CONDUCTOR",
            "clearance_status": "CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR",
            "eta_status": "ETA_NOT_FINAL",
            "meter_per_px": None,
            "reason_codes": ["TREE_DETECTED_BUT_POLE_CONDUCTOR_NOT_READY"],
            "no_fake_clearance": True,
        }

    if not reference_valid:
        return {
            "measurement_status": "MEASUREMENT_BLOCKED_NO_VALID_REFERENCE_GEOMETRY",
            "clearance_status": "CLEARANCE_NOT_FINAL_NO_REFERENCE_GEOMETRY",
            "eta_status": "ETA_NOT_FINAL",
            "meter_per_px": None,
            "reason_codes": ["REFERENCE_GEOMETRY_REQUIRED"],
            "no_fake_clearance": True,
        }

    meter_per_px = reference_height_m / reference_pixel_height

    return {
        "measurement_status": "MEASUREMENT_REFERENCE_READY_BUT_CLEARANCE_NEEDS_PAIRING",
        "clearance_status": "CLEARANCE_NOT_FINAL_PAIRING_REQUIRED",
        "eta_status": "ETA_NOT_FINAL",
        "meter_per_px": round(meter_per_px, 6),
        "reason_codes": ["REFERENCE_READY", "PAIR_TREE_CONDUCTOR_REQUIRED"],
        "no_fake_clearance": True,
    }


def build_operator_summary(
    frame_info: Dict[str, Any],
    tracking: Dict[str, Any],
    edge: Dict[str, Any],
    measurement: Dict[str, Any],
) -> Dict[str, Any]:
    detections = tracking.get("tracked_detections", [])

    return {
        "operator_status": "SESSION_MEASUREMENT_DIAGNOSTIC_READY",
        "frame_status": frame_info.get("status"),
        "tracking_status": tracking.get("tracking_status"),
        "track_id_seen": tracking.get("track_id_seen"),
        "active_track_count": tracking.get("active_track_count"),
        "tree_detected_candidate": any(str(d.get("class_name")) == "pohon_sono" for d in detections),
        "detection_count": len(detections),
        "edge_status": edge.get("edge_status"),
        "measurement_status": measurement.get("measurement_status"),
        "clearance_status": measurement.get("clearance_status"),
        "eta_status": measurement.get("eta_status"),
        "report_status": "LOCAL_SESSION_OUTPUT_READY",
        "spreadsheet_status": "SPREADSHEET_READY_AFTER_SHUTTER",
        "map_status": "MAP_READY_IF_GPS_VALID",
        "no_fake_detection": True,
        "no_fake_clearance": True,
        "no_fake_gps": True,
        "production_status": "NOT_FINAL_FIELD_TRIAL_DIAGNOSTIC",
    }


def process_frame_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    global _FRAME_INDEX
    _FRAME_INDEX += 1

    started = time.time()

    frame_b64 = (
        payload.get("frame_base64")
        or payload.get("image_base64")
        or payload.get("image")
        or payload.get("frame")
        or ""
    )

    frame, frame_info = decode_frame_base64(str(frame_b64))

    if frame is None:
        return {
            "ok": True,
            "status": "FRAME_NOT_PROCESSED_DECODE_FAILED",
            "frame": frame_info,
            "tracking": {
                "tracking_status": "TRACKING_NOT_RUN_FRAME_DECODE_FAILED",
                "track_id_seen": False,
                "active_track_count": 0,
                "tracked_detections": [],
            },
            "edge": {
                "edge_status": "EDGE_NOT_RUN_FRAME_DECODE_FAILED",
                "edge_refinement_final": False,
                "items": [],
            },
            "measurement": {
                "measurement_status": "MEASUREMENT_NOT_READY_NO_FRAME",
                "clearance_status": "CLEARANCE_NOT_FINAL",
                "eta_status": "ETA_NOT_FINAL",
                "reason_codes": ["FRAME_DECODE_FAILED"],
                "no_fake_clearance": True,
            },
            "no_fake_detection": True,
            "no_fake_clearance": True,
            "runtime_mode": "YOLO_FIRST_TRACKING_MEASUREMENT_DIAGNOSTIC",
        }

    detections: List[Dict[str, Any]] = []

    # Hanya untuk synthetic smoke agar bisa membuktikan tracking ID tidak flicker.
    # Field runtime tetap mengandalkan YOLO-first route yang sudah dikunci di 6.27.
    if payload.get("synthetic_smoke") is True:
        detections = _detect_green_synthetic_target(frame)

    tracking = _TRACKER.update(detections, _FRAME_INDEX)
    edge = edge_refinement_diagnostic(frame, tracking.get("tracked_detections", []))
    measurement = measurement_guard(
        tracking.get("tracked_detections", []),
        manual_reference=payload.get("manual_reference") if isinstance(payload.get("manual_reference"), dict) else None,
    )
    summary = build_operator_summary(frame_info, tracking, edge, measurement)

    latency_ms = int((time.time() - started) * 1000)

    return {
        "ok": True,
        "version": "progress6_28_tracking_measurement_runtime",
        "timestamp": now_iso(),
        "session_id": payload.get("session_id", ""),
        "runtime_mode": "YOLO_FIRST_TRACKING_MEASUREMENT_DIAGNOSTIC",
        "latency_ms": latency_ms,
        "frame": frame_info,
        "tracking": tracking,
        "edge": edge,
        "measurement": measurement,
        "operator_summary": summary,
        "no_fake_detection": True,
        "no_fake_clearance": True,
        "no_fake_gps": True,
        "model_status": "TREE_MODEL_READY_CANDIDATE" if TREE_MODEL_PATH.exists() else "TREE_MODEL_NOT_READY",
        "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
        "pole_model_status": "POLE_MODEL_NOT_READY",
        "clearance_status": measurement.get("clearance_status"),
        "eta_status": measurement.get("eta_status"),
    }


def install_progress6_28_tracking_measurement(app: Any) -> Any:
    if getattr(app, "_progress6_28_tracking_measurement_installed", False):
        return app

    @app.post("/api/field/session/progress6-28-diagnostic-frame")
    def progress6_28_diagnostic_frame():  # type: ignore[unused-ignore]
        try:
            from flask import jsonify, request
            payload = request.get_json(silent=True) or {}
            if not isinstance(payload, dict):
                payload = {}
            return jsonify(process_frame_payload(payload)), 200
        except Exception as exc:
            from flask import jsonify
            return jsonify(
                {
                    "ok": False,
                    "status": "PROGRESS6_28_DIAGNOSTIC_EXCEPTION",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "no_fake_detection": True,
                    "no_fake_clearance": True,
                }
            ), 200

    app._progress6_28_tracking_measurement_installed = True
    return app


def make_synthetic_frame_base64(offset_x: int = 0) -> str:
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (25, 38, 34)

    x1 = 220 + int(offset_x)
    y1 = 90
    x2 = 420 + int(offset_x)
    y2 = 390

    cv2.rectangle(img, (x1, y1), (x2, y2), (45, 150, 70), -1)
    cv2.rectangle(img, (x1, y1), (x2, y2), (180, 255, 190), 3)
    cv2.putText(img, "pohon_sono synthetic", (150, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 255, 230), 2)

    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("JPEG_ENCODE_FAILED")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


__all__ = [
    "process_frame_payload",
    "install_progress6_28_tracking_measurement",
    "make_synthetic_frame_base64",
    "decode_frame_base64",
    "edge_refinement_diagnostic",
    "measurement_guard",
]
