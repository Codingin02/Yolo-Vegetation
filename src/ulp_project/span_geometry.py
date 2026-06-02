"""Span and cable geometry helpers."""

from __future__ import annotations

from math import hypot
from typing import Any


def bbox_center(bbox: list[float] | tuple[float, float, float, float] | None) -> tuple[float, float] | None:
    if not bbox or len(bbox) != 4:
        return None
    x1, y1, x2, y2 = [float(value) for value in bbox]
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def bbox_gap_pixels(a: list[float] | None, b: list[float] | None) -> float | None:
    if not a or not b or len(a) != 4 or len(b) != 4:
        return None
    ax1, ay1, ax2, ay2 = [float(value) for value in a]
    bx1, by1, bx2, by2 = [float(value) for value in b]
    dx = max(bx1 - ax2, ax1 - bx2, 0.0)
    dy = max(by1 - ay2, ay1 - by2, 0.0)
    return hypot(dx, dy)


def estimate_span_midpoint(pole_a: dict[str, Any], pole_b: dict[str, Any]) -> dict[str, Any]:
    a_center = bbox_center(pole_a.get("bbox"))
    b_center = bbox_center(pole_b.get("bbox"))
    if a_center is None or b_center is None:
        return {"status": "SPAN_GEOMETRY_NOT_READY", "midpoint": None, "reason": "pole_bbox_missing"}
    midpoint = ((a_center[0] + b_center[0]) / 2.0, (a_center[1] + b_center[1]) / 2.0)
    return {"status": "SPAN_GEOMETRY_READY", "midpoint": midpoint, "reason": ""}


def infer_nearest_asset_type(asset_type: str | None) -> str:
    normalized = (asset_type or "").strip().lower()
    if normalized in {"conductor", "kabel", "cable"}:
        return "conductor"
    if normalized in {"span", "bentang"}:
        return "span"
    if normalized in {"transformer", "trafo"}:
        return "transformer"
    if normalized in {"pole", "tiang", "struktur_penyangga"}:
        return "pole"
    return "unknown"
