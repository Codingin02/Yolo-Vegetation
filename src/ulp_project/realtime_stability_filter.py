"""Rolling stability filter for realtime candidate detections."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

WINDOW_SECONDS = 33.0
MIN_FRAMES = 5
_WINDOWS: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
_LATEST_CONFIRMED: dict[str, dict[str, Any]] = {}


def reset_stability_filter(session_id: str | None = None) -> None:
    if session_id:
        _WINDOWS.pop(session_id, None)
        _LATEST_CONFIRMED.pop(session_id, None)
        return
    _WINDOWS.clear()
    _LATEST_CONFIRMED.clear()


def apply_stability_filter(session_id: str, frame_result: dict[str, Any], *, now: float | None = None) -> dict[str, Any]:
    stamp = float(now if now is not None else time.time())
    window = _WINDOWS[session_id]
    frame = {"timestamp": stamp, **frame_result}
    window.append(frame)
    while window and stamp - float(window[0].get("timestamp", stamp)) > WINDOW_SECONDS:
        window.popleft()

    if len(window) < MIN_FRAMES:
        return {
            **frame_result,
            "stability_status": "STABILIZING",
            "published_result_status": "UNSTABLE_DETECTION_NOT_PUBLISHED",
            "stable_window_frame_count": len(window),
            "latest_confirmed_result": _LATEST_CONFIRMED.get(session_id),
            "no_spam_report_per_frame": True,
        }

    tree_votes = sum(1 for item in window if bool(item.get("tree_detected")))
    pole_votes = sum(1 for item in window if bool(item.get("pole_detected")))
    conductor_votes = sum(1 for item in window if bool(item.get("conductor_detected")))
    majority = len(window) // 2 + 1
    stable = {
        "tree_detected": tree_votes >= majority,
        "pole_detected": pole_votes >= majority,
        "conductor_detected": conductor_votes >= majority,
        "detected_classes": _majority_classes(window, majority),
        "geometry_status": _stable_geometry_status(window),
        "stability_status": "STABLE_CANDIDATE_READY",
        "published_result_status": "STABLE_CANDIDATE_READY",
        "stable_window_frame_count": len(window),
        "stable_window_seconds": round(stamp - float(window[0].get("timestamp", stamp)), 3),
        "no_spam_report_per_frame": True,
    }
    if not stable["tree_detected"] and session_id in _LATEST_CONFIRMED:
        return {
            **frame_result,
            "stability_status": "LATEST_CONFIRMED_RESULT_HELD",
            "published_result_status": "LATEST_CONFIRMED_RESULT_HELD",
            "latest_confirmed_result": _LATEST_CONFIRMED[session_id],
            "stable_window_frame_count": len(window),
            "no_spam_report_per_frame": True,
        }
    _LATEST_CONFIRMED[session_id] = {**frame_result, **stable}
    return {**frame_result, **stable, "latest_confirmed_result": _LATEST_CONFIRMED[session_id]}


def _majority_classes(window: deque[dict[str, Any]], majority: int) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for item in window:
        for name in item.get("detected_classes") or []:
            counts[str(name)] += 1
    return sorted(name for name, count in counts.items() if count >= majority)


def _stable_geometry_status(window: deque[dict[str, Any]]) -> str:
    statuses = [str(item.get("geometry_status") or item.get("measurement_result", {}).get("geometry_status") or "") for item in window]
    if statuses.count("GEOMETRY_READY_CANDIDATE") >= (len(window) // 2 + 1):
        return "GEOMETRY_READY_CANDIDATE"
    if any("BLOCKED" in status for status in statuses):
        return "GEOMETRY_BLOCKED_NO_MULTICLASS_MODEL"
    return "GEOMETRY_STABILIZING"
