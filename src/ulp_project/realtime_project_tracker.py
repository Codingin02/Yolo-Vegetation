from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

_SESSIONS: Dict[str, Dict[str, Any]] = {}
_NEXT_ID = 1

PROJECT_CLASSES = {"pohon_sono", "konduktor", "struktur_penyangga"}


def _iou(a: List[float], b: List[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    denom = area_a + area_b - inter
    if denom <= 0:
        return 0.0
    return inter / denom


def _smooth_box(old_box: List[float], new_box: List[float], alpha: float = 0.65) -> List[float]:
    if not old_box or len(old_box) != 4:
        return list(new_box)
    return [
        float(alpha * new_box[0] + (1.0 - alpha) * old_box[0]),
        float(alpha * new_box[1] + (1.0 - alpha) * old_box[1]),
        float(alpha * new_box[2] + (1.0 - alpha) * old_box[2]),
        float(alpha * new_box[3] + (1.0 - alpha) * old_box[3]),
    ]


def reset_tracks(session_id: str) -> Dict[str, Any]:
    _SESSIONS.pop(session_id, None)
    return {"ok": True, "status": "TRACKS_RESET", "session_id": session_id}


def assign_stable_track_ids(
    detections: List[Dict[str, Any]],
    session_id: str,
    max_lost_frames: int = 8,
    iou_threshold: float = 0.30,
) -> List[Dict[str, Any]]:
    global _NEXT_ID

    if not session_id:
        session_id = "UNKNOWN_SESSION"

    now = time.time()
    state = _SESSIONS.setdefault(session_id, {"tracks": {}, "frame_index": 0})
    state["frame_index"] += 1
    frame_index = state["frame_index"]
    tracks: Dict[int, Dict[str, Any]] = state["tracks"]

    filtered = []
    for det in detections or []:
        class_name = str(det.get("class_name") or det.get("object_group") or "").strip()
        if class_name not in PROJECT_CLASSES:
            continue
        box = det.get("bbox_xyxy_px")
        if not isinstance(box, list) or len(box) != 4:
            continue
        filtered.append(det)

    assigned_track_ids = set()
    assigned_detection_indices = set()

    for det_idx, det in enumerate(filtered):
        class_name = det["class_name"]
        box = [float(v) for v in det["bbox_xyxy_px"]]

        best_track_id = None
        best_iou = 0.0

        for tid, tr in tracks.items():
            if tid in assigned_track_ids:
                continue
            if tr.get("class_name") != class_name:
                continue
            candidate_iou = _iou(box, tr.get("bbox_xyxy_px", [0, 0, 0, 0]))
            if candidate_iou > best_iou:
                best_iou = candidate_iou
                best_track_id = tid

        if best_track_id is not None and best_iou >= iou_threshold:
            tr = tracks[best_track_id]
            smoothed_box = _smooth_box(tr.get("bbox_xyxy_px", box), box)
            tr.update(
                {
                    "bbox_xyxy_px": smoothed_box,
                    "last_seen_frame": frame_index,
                    "last_seen_ts": now,
                    "lost_frames": 0,
                    "confidence": det.get("confidence"),
                }
            )
            det["track_id"] = int(best_track_id)
            det["bbox_xyxy_px"] = smoothed_box
            det["track_status"] = "TRACK_UPDATED"
            assigned_track_ids.add(best_track_id)
            assigned_detection_indices.add(det_idx)
        else:
            tid = _NEXT_ID
            _NEXT_ID += 1
            tracks[tid] = {
                "track_id": tid,
                "class_name": class_name,
                "bbox_xyxy_px": box,
                "last_seen_frame": frame_index,
                "last_seen_ts": now,
                "lost_frames": 0,
                "confidence": det.get("confidence"),
            }
            det["track_id"] = int(tid)
            det["track_status"] = "TRACK_NEW"
            assigned_track_ids.add(tid)
            assigned_detection_indices.add(det_idx)

    for tid, tr in list(tracks.items()):
        if tid in assigned_track_ids:
            continue
        lost = int(frame_index - int(tr.get("last_seen_frame", frame_index)))
        tr["lost_frames"] = lost
        if lost > max_lost_frames:
            tracks.pop(tid, None)

    return filtered


def keep_tracks_for_lost_frames(session_id: str, max_lost_frames: int = 8) -> List[Dict[str, Any]]:
    state = _SESSIONS.get(session_id) or {}
    frame_index = int(state.get("frame_index", 0))
    tracks = state.get("tracks", {})
    out = []
    for tid, tr in tracks.items():
        lost = int(frame_index - int(tr.get("last_seen_frame", frame_index)))
        if 0 < lost <= max_lost_frames:
            out.append(
                {
                    "track_id": int(tid),
                    "class_name": tr.get("class_name"),
                    "object_group": tr.get("class_name"),
                    "confidence": tr.get("confidence"),
                    "bbox_xyxy_px": tr.get("bbox_xyxy_px"),
                    "track_status": "TRACK_PREDICTED_SHORT_GAP",
                    "lost_frames": lost,
                    "source": "TRACKER_SHORT_GAP",
                }
            )
    return out


def smooth_bbox(session_id: str, detection: Dict[str, Any]) -> Dict[str, Any]:
    return detection
