"""Span/conductor geometry estimation helpers."""

from __future__ import annotations

from typing import Any


def estimate_span_lowest_point(points: list[tuple[float, float]]) -> dict[str, Any]:
    if len(points) < 2:
        return {"status": "SPAN_NOT_DETECTED", "lowest_point": None, "reason": "Need at least two conductor/span points."}
    # Image coordinates use larger y as lower in the frame.
    lowest = max(points, key=lambda item: item[1])
    mid_x = (min(point[0] for point in points) + max(point[0] for point in points)) / 2.0
    nearest_mid = min(points, key=lambda item: abs(item[0] - mid_x))
    return {
        "status": "SPAN_LOWEST_POINT_READY",
        "lowest_point": {"x": lowest[0], "y": lowest[1]},
        "midpoint_candidate": {"x": nearest_mid[0], "y": nearest_mid[1]},
        "reason": "Lowest image y among conductor/span points is used as conservative sag point.",
    }


def span_points_from_detections(detections: list[dict[str, Any]]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for detection in detections:
        bbox = detection.get("bbox")
        if not bbox:
            continue
        x = (float(bbox[0]) + float(bbox[2])) / 2.0
        y = (float(bbox[1]) + float(bbox[3])) / 2.0
        points.append((x, y))
    return points
