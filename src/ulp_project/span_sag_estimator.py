"""Span sag status helpers without inventing PLN final geometry."""

from __future__ import annotations

from typing import Any


def estimate_span_sag(points: list[dict[str, float]] | None) -> dict[str, Any]:
    if not points:
        return {"span_sag_status": "SPAN_NOT_DETECTED", "estimated_lowest_span_point_m": None}
    lowest = max(points, key=lambda item: item.get("y", 0.0))
    return {"span_sag_status": "SPAN_LOWEST_POINT_ESTIMATED_FROM_VISIBLE_POINTS", "lowest_point": lowest, "estimated_lowest_span_point_m": lowest.get("height_m")}


def asset_visibility_status(tree_visible: bool, structure_visible: bool, asset_visible: bool) -> str:
    if not asset_visible and structure_visible:
        return "STRUCTURE_VISIBLE_ASSET_MISSING"
    if tree_visible and not asset_visible:
        return "TREE_VISIBLE_ASSET_MISSING"
    if not asset_visible:
        return "ASSET_NOT_DETECTED"
    return "ASSET_VISIBLE"
